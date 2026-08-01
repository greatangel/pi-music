# Pi Music - Discord Music Bot

A lightweight, high-performance Discord music bot optimized for Raspberry Pi. Powered by `discord.py`, `wavelink`, and a standalone Lavalink v4 audio server with YouTube OAuth support to prevent IP blocking and rate limits.

## Features

- **Ultra-low CPU usage** on Raspberry Pi (audio decoding/streaming is offloaded to Lavalink)
- Play music from **YouTube, SoundCloud, and direct streams** (URL or search query)
- **YouTube OAuth2 support** to bypass bot detection and rate limits
- Queue management (add, remove, clear, shuffle)
- Playback controls (pause, resume, skip, now playing)
- Multi-guild support

---

## Quick Start (Docker & Portainer Stack)

### 1. Prepare environment

Clone your repository on your host machine or Raspberry Pi:

```bash
git clone https://github.com/greatangel/pi-music.git
cd pi-music
cp .env.example .env
# Edit .env and set your DISCORD_TOKEN
```

### 2. Deploy via Portainer (Repository / Stack Method)

1. Open **Portainer → Stacks → Add stack**.
2. **Name:** `pi-music`
3. **Repository URL:** `https://github.com/greatangel/pi-music`
4. **Compose path:** `docker-compose.yml`
5. **Add Environment Variable:** `DISCORD_TOKEN=your_token_here`
6. Click **Deploy the stack**.

---

## YouTube Authorization Setup (One-time)

Because YouTube blocks automated server requests, Lavalink uses the official `youtube-plugin` with OAuth2.

1. After deploying the stack, view the logs for the `lavalink` container in Portainer (or run `docker logs -f lavalink`).
2. Look for a message containing a Google activation link and code:

   ```
   Go to https://www.google.com/device and enter code XXX-XXX-XXX
   ```

3. Open the link in a browser, enter the code, and approve access using a **burner Google account**.
4. Lavalink will save the authorization token, and your bot will stream seamlessly.

---

## Commands

| Command | Description |
|---------|-------------|
| `!join` | Join your voice channel |
| `!play <url or query>` | Play track from YouTube/SoundCloud |
| `!skip` | Skip current song |
| `!queue` | Show current queue |
| `!pause` | Pause playback |
| `!resume` | Resume playback |
| `!now` | Show currently playing song |
| `!remove <num>` | Remove song from queue by position |
| `!clear` | Clear queue |
| `!shuffle` | Shuffle queue |
| `!leave` | Disconnect bot |
| `!help` | Show help menu |

---

## Requirements

- **Docker & Docker Compose**
- **Discord Bot Token** with *Message Content Intent* enabled in the [Discord Developer Portal](https://discord.com/developers/applications)

---

## Project Structure

```
pi-music/
├── bot.py              # Main Discord bot code (wavelink)
├── requirements.txt    # Python dependencies (discord.py, wavelink)
├── Dockerfile          # Lightweight Python container definition
├── application.yml     # Lavalink server configuration & plugin definitions
├── docker-compose.yml  # Multi-container stack (Bot + Lavalink)
└── .env.example        # Environment variable template
```

---

## Technical Details (Raspberry Pi Optimizations)

- **Architecture:** Runs 2 containers (Python bot + Lavalink v4 JVM node).
- **DNS Handling:** Designed to work alongside host Pi-hole without DNS loop issues (using `daemon.json` custom DNS resolvers if needed).
- **Resource Footprint:** Offloads audio processing to Java, reducing memory footprint and preventing Python process stalls on ARM64 single-board computers.

---

## Updating

In Portainer:

1. Go to **Stacks → pi-music**.
2. Click **Git ops / Editor → Pull and redeploy**.
