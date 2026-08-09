# Nyx Pinguin // Discord Audio Broadcaster

Nyx Pinguin is a robust, multi-component Discord bot and web dashboard designed to broadcast live audio from a "speaker" in a single source voice channel to multiple "listener" bots scattered across various destination voice channels. 

It is ideal for live events, multi-channel announcements, and server-wide audio distribution without dropping audio quality or increasing latency unnecessarily.

## 🏗️ Architecture

The project is split into three main microservices that communicate via a shared MongoDB database.

1. **`bot-node/` (Audio Engine - Node.js)**
   - Powered by `discord.js` and `@discordjs/voice`.
   - Connects to Discord voice channels directly.
   - Captures raw Opus audio packets from the source channel and dynamically clones/routes them to the destination bots without transcoding, ensuring ultra-low latency.
   - Listens to commands via IPC (Inter-Process Communication) and streams its logs to the database.

2. **`backend/` (API & Web Server - Python / FastAPI)**
   - Handles the Discord OAuth2 authentication for dashboard access.
   - Interacts with the Discord API to dynamically fetch servers, channels, and roles.
   - Saves configurations in MongoDB and uses a Tailable Cursor to send real-time commands (IPC) to the Node.js bot.
   - Serves the frontend application.

3. **`frontend/` (Dashboard - Vue 3 + Tailwind CSS + Vite)**
   - A cyberpunk/matrix-themed dashboard interface.
   - Allows server administrators to configure the Source Channel, Authorized Speaker Role, and Destination Channels using intuitive dropdowns and checkboxes.
   - Includes a live terminal for viewing the Node.js bot's logs in real-time.

---

## 🚀 Prerequisites

- **Node.js** (v18+)
- **Python** (v3.10+)
- **MongoDB** (local or Atlas)
- **A Discord Developer Application** with a Bot Token and OAuth2 configured.

---

## ⚙️ Setup & Installation

### 1. Database & Environment

1. Rename the `dab-project/.env.example` to `dab-project/.env` (or create a `.env` in the `backend/` folder).
2. Fill in the required values:
   ```env
   # Discord Dev Portal
   DISCORD_CLIENT_ID=your_client_id
   DISCORD_CLIENT_SECRET=your_client_secret
   DISCORD_REDIRECT_URI=http://localhost:8000/api/oauth/callback # update for prod

   # Discord Bot Tokens
   DISCORD_PRIMARY_TOKEN=your_main_bot_token
   DISCORD_AUX_TOKENS=comma,separated,list,of,secondary,bot,tokens

   # Database
   MONGO_URI=mongodb://localhost:27017
   MONGO_DB_NAME=discord_pinguin
   ```

### 2. Backend (FastAPI)

```bash
cd dab-project/backend
python -m venv .venv
# On Windows: .venv\Scripts\activate
# On Mac/Linux: source .venv/bin/activate
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
*(Once built, the Python backend will automatically serve the static files from the `dist/` folder when accessing `http://localhost:8000`)*. 
*(If you want to run the frontend in dev mode with hot-reloading, run `npm run dev` and access it on the Vite port).*

### 4. Audio Engine (Node Bot)

```bash
cd dab-project/bot-node
npm install
npm start
```
*The bot will connect to Discord and wait for configuration updates via MongoDB.*

---

## 🎛️ Usage

1. Go to `http://localhost:8000` (or your production URL).
2. Click **Authenticate** to log in via Discord.
3. Enter your **Guild ID** (Server ID) and click **SCAN**.
4. Select the **Source Channel** where the speaker will talk.
5. Select the **Authorized Role** (optional) to filter out background noise from unauthorized users in the source channel.
6. Check the **Destination Channels** where you want the bot clones to join and reproduce the audio.
7. Click **Save to Mainframe**. The bot will immediately connect to the voice channels and start listening/broadcasting.

---

## 📝 License

Proprietary / Internal Use. 
Designed and maintained for [Fiveamtech](https://fiveamtech.it).
