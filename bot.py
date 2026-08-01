import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import wavelink

nodes = [
    wavelink.Node(
        uri="http://192.168.100.99:2281",
        password="youshallnotpass"
    )
]

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable not set")

class PiMusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        # Connect to the Lavalink service defined in docker-compose.yml
        nodes = [
            wavelink.Node(
                uri="http://lavalink:2281",
                password="youshallnotpass"
            )
        ]
        await wavelink.Pool.connect(nodes=nodes, client=self)

bot = PiMusicBot()

@bot.event
async def on_ready():
    print(f'Pi Music connected as {bot.user} (ID: {bot.user.id})')
    print(f'Connected to {len(bot.guilds)} guilds')

@bot.event
async def on_wavelink_node_ready(payload: wavelink.NodeReadyEventPayload):
    print(f"Lavalink Node ready: {payload.node.identifier}")

@bot.event
async def on_wavelink_track_end(payload: wavelink.TrackEndEventPayload):
    """Play the next track in queue automatically when a song finishes."""
    player: wavelink.Player | None = payload.player
    if not player:
        return

    if not player.queue.is_empty:
        next_track = await player.queue.get_wait()
        await player.play(next_track)

@bot.command()
async def join(ctx):
    """Join the user's voice channel"""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect(cls=wavelink.Player)
        await ctx.send(f"Conectado a **{channel.name}**")
    else:
        await ctx.send("Debes estar en un canal de voz.")

@bot.command()
async def play(ctx, *, query: str):
    """Play a song from YouTube/SoundCloud (URL or search query)"""
    if not ctx.author.voice:
        return await ctx.send("Debes estar en un canal de voz.")

    player: wavelink.Player = ctx.voice_client  # type: ignore

    if not player:
        player = await ctx.author.voice.channel.connect(cls=wavelink.Player)

    await ctx.send("🔍 Obteniendo información...")

    # Search using Wavelink (handles both URLs and plain text search queries)
    tracks: wavelink.Search = await wavelink.Playable.search(query)

    if not tracks:
        return await ctx.send("❌ No se encontraron resultados")

    track: wavelink.Playable = tracks[0]

    if player.playing or player.paused:
        await player.queue.put_wait(track)
        await ctx.send(f"🎵 Añadido a la cola: **{track.title}**")
    else:
        await player.play(track)
        await ctx.send(f"▶ Reproduciendo: **{track.title}**")

@bot.command()
async def skip(ctx):
    """Skip the current song"""
    player: wavelink.Player = ctx.voice_client  # type: ignore

    if not player or not player.playing:
        await ctx.send("No hay ninguna canción reproduciéndose")
        return

    await player.skip()
    await ctx.send("⏩ Canción saltada")

@bot.command()
async def queue(ctx):
    """Show the current queue"""
    player: wavelink.Player = ctx.voice_client  # type: ignore

    if not player or player.queue.is_empty:
        await ctx.send("La cola está vacía")
        return

    queue_list = [f"**{i+1}.** {track.title}" for i, track in enumerate(player.queue)]
    display = queue_list[:20]
    msg = "**Cola de reproducción:**\n" + "\n".join(display)
    if len(queue_list) > 20:
        msg += f"\n... y {len(queue_list) - 20} más"
    await ctx.send(msg)

@bot.command()
async def pause(ctx):
    """Pause playback"""
    player: wavelink.Player = ctx.voice_client  # type: ignore

    if player and player.playing:
        await player.pause(True)
        await ctx.send("⏸ Reproducción pausada")
    else:
        await ctx.send("No hay nada reproduciéndose")

@bot.command()
async def resume(ctx):
    """Resume playback"""
    player: wavelink.Player = ctx.voice_client  # type: ignore

    if player and player.paused:
        await player.pause(False)
        await ctx.send("▶ Reproducción reanudada")
    else:
        await ctx.send("La reproducción no está pausada")

@bot.command()
async def remove(ctx, index: int):
    """Remove a song from queue by index (1-based)"""
    player: wavelink.Player = ctx.voice_client  # type: ignore

    if not player or player.queue.is_empty:
        await ctx.send("La cola está vacía")
        return

    if index < 1 or index > len(player.queue):
        await ctx.send("Número de canción inválido")
        return

    removed_track = player.queue.delete(index - 1)
    await ctx.send(f"❌ Canción eliminada: **{removed_track.title}**")

@bot.command()
async def clear(ctx):
    """Clear the entire queue"""
    player: wavelink.Player = ctx.voice_client  # type: ignore

    if not player or player.queue.is_empty:
        await ctx.send("La cola ya está vacía")
        return

    player.queue.clear()
    await ctx.send("🧹 Cola limpiada")

@bot.command()
async def shuffle(ctx):
    """Shuffle the queue"""
    player: wavelink.Player = ctx.voice_client  # type: ignore

    if not player or player.queue.is_empty or len(player.queue) < 2:
        await ctx.send("No hay suficientes canciones en la cola para mezclar")
        return

    player.queue.shuffle()
    await ctx.send("🔀 Cola mezclada")

@bot.command()
async def now(ctx):
    """Show currently playing song"""
    player: wavelink.Player = ctx.voice_client  # type: ignore

    if not player or not player.current:
        await ctx.send("No hay nada reproduciéndose")
        return

    await ctx.send(f"▶ Reproduciendo ahora: **{player.current.title}**")

@bot.command()
async def leave(ctx):
    """Disconnect from voice channel"""
    player: wavelink.Player = ctx.voice_client  # type: ignore
    if player:
        await player.disconnect()
        await ctx.send("Desconectado")
    else:
        await ctx.send("No estoy en un canal de voz.")

@bot.command()
async def help(ctx):
    """Show help message"""
    help_text = """
**Pi Music - Comandos disponibles:**
`!join` - Unirse a tu canal de voz
`!play <url o búsqueda>` - Reproducir canción de YouTube/SoundCloud
`!skip` - Saltar canción actual
`!queue` - Ver cola de reproducción
`!pause` - Pausar reproducción
`!resume` - Reanudar reproducción
`!remove <número>` - Eliminar canción de la cola
`!clear` - Limpiar toda la cola
`!shuffle` - Mezclar cola
`!now` - Ver canción en reproducción
`!leave` - Desconectar bot
`!help` - Mostrar comandos
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
