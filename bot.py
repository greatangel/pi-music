import discord
from discord.ext import commands, tasks
import yt_dlp as youtube_dl
import os
from dotenv import load_dotenv
import asyncio
from youtubesearchpython import VideosSearch
import time
import random

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable not set")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Configuración para yt-dlp - use system ffmpeg (installed in container)
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'quiet': True,
    'no_warnings': True,
}

queues = {}
DISCONNECT_AFTER = 300  # 5 minutes of inactivity
last_activity = {}

# Verificador de inactividad
@tasks.loop(seconds=60)
async def check_inactivity():
    current_time = time.time()
    for guild_id in list(last_activity.keys()):
        guild = bot.get_guild(guild_id)
        if not guild:
            del last_activity[guild_id]
            continue
        
        voice_client = guild.voice_client
        if not voice_client or not voice_client.is_connected():
            del last_activity[guild_id]
            if guild_id in queues:
                del queues[guild_id]
            continue
        
        # Calcular tiempo inactivo
        tiempo_inactivo = current_time - last_activity[guild_id]
        
        # Verificar condiciones para desconectar
        if (
            not voice_client.is_playing() and 
            not queues.get(guild_id, []) and 
            tiempo_inactivo >= DISCONNECT_AFTER
        ):
            await voice_client.disconnect()
            if guild_id in queues:
                del queues[guild_id]
            del last_activity[guild_id]
            print(f"Disconnected due to inactivity in {guild.name}")

def after_playing(error, guild_id):
    if error:
        print(f'Playback error: {error}')
    
    if guild_id in queues and queues[guild_id]:
        next_song = queues[guild_id].pop(0)
        
        guild = bot.get_guild(guild_id)
        if not guild:
            return
        
        voice_client = guild.voice_client
        if not voice_client:
            return
        
        ffmpeg_options = {
            'options': '-vn',
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        }
        source = discord.FFmpegPCMAudio(next_song['url'], **ffmpeg_options)
        voice_client.play(source, after=lambda e: after_playing(e, guild_id))
        
        # Use proper async scheduling instead of run_coroutine_threadsafe
        asyncio.run_coroutine_threadsafe(
            next_song['ctx'].send(f"Reproduciendo: {next_song['title']}"), 
            bot.loop
        )
        
        # Actualizar la última actividad al reproducir nueva canción
        last_activity[guild_id] = time.time()
    else:
        # Iniciar temporizador de desconexión
        last_activity[guild_id] = time.time()

@bot.event
async def on_ready():
    print(f'Pi Music connected as {bot.user} (ID: {bot.user.id})')
    print(f'Connected to {len(bot.guilds)} guilds')
    check_inactivity.start()

@bot.event
async def on_voice_state_update(member, before, after):
    """Track when bot is disconnected manually or moved"""
    if member.id == bot.user.id:
        guild_id = before.channel.guild.id if before.channel else (after.channel.guild.id if after.channel else None)
        if guild_id and before.channel and not after.channel:
            # Bot was disconnected
            if guild_id in queues:
                del queues[guild_id]
            if guild_id in last_activity:
                del last_activity[guild_id]

@bot.command()
async def join(ctx):
    """Join the user's voice channel"""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        await ctx.send(f"Conectado a **{channel.name}**")
    else:
        await ctx.send("Debes estar en un canal de voz.")

@bot.command()
async def play(ctx, *, query: str):
    """Play a song from YouTube (URL or search query)"""
    voice_client = ctx.voice_client

    if not voice_client:
        await ctx.invoke(join)
        voice_client = ctx.voice_client
        if not voice_client:
            return

    # Determinar si es URL o búsqueda
    if not query.startswith(('http://', 'https://', 'www.', 'youtube.com', 'youtu.be')):
        # Buscar en YouTube
        try:
            search = VideosSearch(query, limit=1)
            result = search.result()
            if not result['result']:
                await ctx.send("❌ No se encontraron resultados")
                return
            url = result['result'][0]['link']
        except Exception as e:
            await ctx.send(f"❌ Error en la búsqueda: {e}")
            return
    else:
        url = query

    await ctx.send("🔍 Obteniendo información...")
    
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            url_audio = info['url']
            title = info.get('title', 'Título desconocido')
    except Exception as e:
        await ctx.send(f"❌ Error al obtener audio: {e}")
        return

    song = {
        'url': url_audio,
        'title': title,
        'ctx': ctx
    }

    guild_id = ctx.guild.id
    if guild_id not in queues:
        queues[guild_id] = []
    queues[guild_id].append(song)

    # Actualizar actividad
    last_activity[guild_id] = time.time()

    if not voice_client.is_playing():
        next_song = queues[guild_id].pop(0)
        ffmpeg_options = {
            'options': '-vn',
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        }
        source = discord.FFmpegPCMAudio(next_song['url'], **ffmpeg_options)
        voice_client.play(source, after=lambda e: after_playing(e, guild_id))
        await ctx.send(f"▶ Reproduciendo: **{next_song['title']}**")
    else:
        await ctx.send(f"🎵 Añadido a la cola: **{title}**")

@bot.command()
async def skip(ctx):
    """Skip the current song"""
    voice_client = ctx.voice_client
    
    if not voice_client or not voice_client.is_playing():
        await ctx.send("No hay ninguna canción reproduciéndose")
        return
    
    voice_client.stop()
    await ctx.send("⏩ Canción saltada")

@bot.command()
async def queue(ctx):
    """Show the current queue"""
    guild_id = ctx.guild.id
    
    if not queues.get(guild_id):
        await ctx.send("La cola está vacía")
        return
    
    queue_list = [f"**{i+1}.** {song['title']}" for i, song in enumerate(queues[guild_id])]
    # Limit display to 20 songs to avoid message length issues
    display = queue_list[:20]
    msg = "**Cola de reproducción:**\n" + "\n".join(display)
    if len(queue_list) > 20:
        msg += f"\n... y {len(queue_list) - 20} más"
    await ctx.send(msg)

@bot.command()
async def pause(ctx):
    """Pause playback"""
    voice_client = ctx.voice_client
    
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("⏸ Reproducción pausada")
    else:
        await ctx.send("No hay nada reproduciéndose")

@bot.command()
async def resume(ctx):
    """Resume playback"""
    voice_client = ctx.voice_client
    
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("▶ Reproducción reanudada")
    else:
        await ctx.send("La reproducción no está pausada")

@bot.command()
async def remove(ctx, index: int):
    """Remove a song from queue by index (1-based)"""
    guild_id = ctx.guild.id
    
    if not queues.get(guild_id):
        await ctx.send("La cola está vacía")
        return
    
    if index < 1 or index > len(queues[guild_id]):
        await ctx.send("Número de canción inválido")
        return
    
    removed_song = queues[guild_id].pop(index - 1)
    await ctx.send(f"❌ Canción eliminada: **{removed_song['title']}**")        

@bot.command()
async def clear(ctx):
    """Clear the entire queue"""
    guild_id = ctx.guild.id
    
    if not queues.get(guild_id):
        await ctx.send("La cola ya está vacía")
        return
    
    queues[guild_id].clear()
    await ctx.send("🧹 Cola limpiada")

@bot.command()
async def shuffle(ctx):
    """Shuffle the queue"""
    guild_id = ctx.guild.id
    
    if not queues.get(guild_id) or len(queues[guild_id]) < 2:
        await ctx.send("No hay suficientes canciones en la cola para mezclar")
        return
    
    random.shuffle(queues[guild_id])
    await ctx.send("🔀 Cola mezclada")

@bot.command()
async def now(ctx):
    """Show currently playing song"""
    voice_client = ctx.voice_client
    guild_id = ctx.guild.id
    
    if not voice_client or not voice_client.is_playing():
        await ctx.send("No hay nada reproduciéndose")
        return
    
    # We don't track current song easily, so just show queue[0] if playing
    await ctx.send("Use `!queue` to see what's playing (first item)")

@bot.command()
async def leave(ctx):
    """Disconnect from voice channel"""
    if ctx.voice_client:
        guild_id = ctx.guild.id
        if guild_id in queues:
            del queues[guild_id]
        if guild_id in last_activity:
            del last_activity[guild_id]
        await ctx.voice_client.disconnect()
        await ctx.send("Desconectado")
    else:
        await ctx.send("No estoy en un canal de voz.")

@bot.command()
async def help(ctx):
    """Show help message"""
    help_text = """
**Pi Music - Comandos disponibles:**
`!join` - Unirse a tu canal de voz
`!play <url o búsqueda>` - Reproducir canción de YouTube
`!skip` - Saltar canción actual
`!queue` - Ver cola de reproducción
`!pause` - Pausar reproducción
`!resume` - Reanudar reproducción
`!remove <número>` - Eliminar canción de la cola
`!clear` - Limpiar toda la cola
`!shuffle` - Mezclar cola
`!leave` - Desconectar bot
`!help` - Mostrar esta ayuda
    """
    await ctx.send(help_text)

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Falta argumento requerido: {error.param.name}")
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send(f"Argumento inválido: {error}")
        return
    print(f"Command error: {error}")
    await ctx.send("Ocurrió un error al ejecutar el comando")

bot.run(TOKEN)