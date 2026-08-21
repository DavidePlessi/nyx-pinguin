# Nyx Pinguin // Advanced Guild System

Nyx Pinguin is a robust, multi-component Discord bot and web dashboard designed to manage various aspects of a gaming guild. Originally built as a Discord Audio Broadcaster, it has evolved into a comprehensive suite including a real-time Audio Matrix, a Music Player, and an advanced Loot/Drop Management System connected to Questlog.

## 🏗️ Architecture

The project is split into four main microservices that communicate via a shared MongoDB database.

1. **`bot-node/` (Audio & Music Engine - Node.js)**
   - Powered by `discord.js` and `@discordjs/voice`.
   - **Audio Matrix**: Captures raw Opus audio packets from a source channel and dynamically clones/routes them to destination bots without transcoding, ensuring ultra-low latency for cross-channel or cross-server broadcasting.
   - **Music Player**: Includes a complete music streaming engine for playing audio tracks inside Discord voice channels.
   - Listens to commands via IPC (Inter-Process Communication) and streams its logs to the database.

2. **`guild-bot/` (Guild & Drops Manager - Python / discord.py)**
   - Handles slash commands for the server (e.g., `/pinguin_drop_start`, `/pinguin_drop_cancel`).
   - Manages interactive Discord UI components (Views/Buttons) to allow users to apply for drops directly from Discord.
   - Integrates with the Questlog API to fetch item details and thumbnails dynamically.

3. **`backend/` (API & Web Server - Python / FastAPI)**
   - Handles Discord OAuth2 authentication for dashboard access.
   - Saves configurations in MongoDB and uses a Tailable Cursor to send real-time commands to the Node.js bot.
   - Provides REST endpoints for User Management, Build Management, and Drop Poll Assignment.
   - Uses HTTPX to dispatch cross-service announcements (like declaring a drop winner) directly to Discord.
   - Serves the frontend application.

4. **`frontend/` (Dashboard - Vue 3 + Tailwind CSS + Vite)**
   - A cyberpunk/matrix-themed dashboard interface with full i18n support (EN, IT, ES, FR, DE).
   - **Broadcasting**: Configure Source Channels, Authorized Speaker Roles, and Destination Channels.
   - **Drops System**: Users can draft their in-game builds (importing via Questlog links) and request "Primary" status approval.
   - **Drops Admin**: Guild leaders can review builds, manage active Drop Polls, kick/add candidates, and assign drops, keeping a persistent historical record of all assignments.

---

## 🚀 Prerequisites

- **Node.js** (v18+)
- **Python** (v3.10+)
- **MongoDB** (local or Atlas)
- **Discord Developer Applications** with Bot Tokens and OAuth2 configured.

---

## ⚙️ Setup & Installation

### 1. Database & Environment

Rename the `.env.example` files to `.env` and fill in the required values:
```env
# Discord Dev Portal
DISCORD_CLIENT_ID=your_client_id
DISCORD_CLIENT_SECRET=your_client_secret
DISCORD_REDIRECT_URI=http://localhost:8000/api/oauth/callback

# Discord Bot Tokens
DISCORD_PRIMARY_TOKEN=your_main_node_bot_token
DISCORD_AUX_TOKENS=comma,separated,list,of,secondary,bot,tokens
GUILD_BOT_TOKEN=your_python_guild_bot_token

# Database
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=discord_pinguin
```

### 2. Backend (FastAPI)

```bash
cd dab-project/backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main_api.py
```
*The backend will run on `http://localhost:8000`.*

### 3. Frontend (Vue 3)

```bash
cd dab-project/frontend
npm install
npm run build
```
*(Once built, the Python backend will automatically serve the static files. For dev mode, run `npm run dev`)*.

### 4. Audio Engine (Node Bot)

```bash
cd dab-project/bot-node
npm install
npm start
```

### 5. Guild Bot (Python)

```bash
cd guild-bot
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

*Alternatively, you can run the entire stack using Docker Compose: `docker-compose up -d --build`.*

---

## 🕹️ Key Features & Usage

### 🎙️ Audio Broadcasting (Matrix)
Configure audio routing from the web dashboard. The "Listener" bot captures audio from the source channel and forwards it to the "Speaker" bots in destination channels.

### ⚔️ Build Management
Users log into the dashboard via Discord, navigate to the **Drops System**, and paste their Questlog build URL. The system automatically fetches the equipment. Once saved, users can request Admin approval to set it as their **Primary Build**.

### 🎁 Drop Polls & Assignment
1. An admin starts a drop poll in Discord using `/pinguin_drop_start <item_name>`.
2. Users click the **Apply** button on the interactive Discord message. The bot verifies if the requested item is present in their approved Primary Build.
3. Admins visit the **Drops Management** web interface to review applicants, approve the winner, or cancel the drop.
4. The backend automatically closes the poll, removes the interactive buttons from Discord, and posts an official announcement with the winner and participants.

---

## 📜 License

Proprietary / Internal Use. 
Designed and maintained for [Fiveamtech](https://fiveamtech.it).
