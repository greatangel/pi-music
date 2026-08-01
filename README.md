# Pi Music - Discord Music Bot

A Discord music bot that plays audio from YouTube. Built with discord.py, yt-dlp, and FFmpeg.

## Features
- Play music from YouTube (URL or search query)
- Queue management (add, remove, clear, shuffle)
- Playback controls (pause, resume, skip)
- Auto-disconnect after inactivity (5 minutes)
- Multi-guild support

## Quick Start (Docker + Portainer)

### 1. Prepare environment
```bash
cd /opt/data/workplace/pi-music
cp .env.example .env
# Edit .env and add your DISCORD_TOKEN
```

### 2. Build and run with Docker Compose
```bash
docker compose up -d --build
```

### 3. Deploy via Portainer
1. Open Portainer → Stacks → Add stack
2. Name: `pi-music`
3. Paste the contents of `docker-compose.yml`
4. Add environment variable: `DISCORD_TOKEN=your_token_here`
5. Deploy

## Manual Docker (without compose)
```bash
# Build
docker build -t pi-music .

# Run
docker run -d \
  --name pi-music \
  --restart unless-stopped \
  -e DISCORD_TOKEN=your_token_here \
  -e TZ=America/Monterrey \
  pi-music
```

## Commands
| Command | Description |
|---------|-------------|
| `!join` | Join your voice channel |
| `!play <url or search>` | Play from YouTube |
| `!skip` | Skip current song |
| `!queue` | Show queue |
| `!pause` | Pause playback |
| `!resume` | Resume playback |
| `!remove <num>` | Remove song from queue |
| `!clear` | Clear queue |
| `!shuffle` | Shuffle queue |
| `!leave` | Disconnect bot |
| `!help` | Show help |

## Requirements
- Python 3.11+
- FFmpeg (included in Docker image)
- Discord bot token with message content intent enabled

## Project Structure
```
pi-music/
├── bot.py              # Main bot code
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container definition
├── docker-compose.yml  # Portainer stack config
└── .env.example        # Environment template
```

## Notes for Raspberry Pi
- Image uses `python:3.11-slim-bookworm` (ARM64 compatible)
- Memory limited to 512MB in compose
- FFmpeg and Opus libraries pre-installed
- Runs as non-root user for security

## Updating
```bash
cd /opt/data/workplace/pi-music
git pull  # if using git
docker compose up -d --build  # rebuild and restart
```

Or in Portainer: Stack → pi-music → Editor → Update the stack → Pull image & Recreate