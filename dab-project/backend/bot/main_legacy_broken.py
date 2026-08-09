import discord
import asyncio
import os
import sys
import queue

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.db import init_db
from app.core.ipc import listen_channel, publish_message, init_ipc
from bot.audio import BroadcastSink, BroadcastSource
from app.models.models import GuildConfig

primary_bot = discord.Bot()
aux_bots = []
aux_tokens = [t.strip() for t in settings.DISCORD_AUX_TOKENS.split(",") if t.strip()]

for _ in aux_tokens:
    aux_bots.append(discord.Bot())

# Central audio router
global_sink = BroadcastSink()

@primary_bot.slash_command(name="pinguin_on_duty", description="Avvia il broadcasting audio dai canali configurati")
async def pinguin_on_duty(ctx: discord.ApplicationContext):
    await ctx.defer()
    config = await GuildConfig.find_one(GuildConfig.guild_id == str(ctx.guild_id))
    if not config or not config.is_active or not config.source_channel_id:
        await ctx.followup.send("❌ Nessuna configurazione attiva per questo server o canale sorgente mancante. Configuralo prima dalla Dashboard Web.")
        return
        
    await publish_message("dab_updates", {
        "action": "start_broadcast",
        "guild_id": str(ctx.guild_id),
        "source_channel_id": config.source_channel_id,
        "dest_channels": config.dest_channels
    })
    await ctx.followup.send(f"🐧 **Pinguin on Duty!** Avvio del broadcasting dal canale <#{config.source_channel_id}> verso {len(config.dest_channels)} canali di destinazione...")

@primary_bot.slash_command(name="pinguin_at_ease", description="Ferma il broadcasting audio")
async def pinguin_at_ease(ctx: discord.ApplicationContext):
    await publish_message("dab_updates", {
        "action": "stop_broadcast",
        "guild_id": str(ctx.guild_id)
    })
    await ctx.respond("💤 **Pinguin at Ease.** Broadcasting fermato!")




@primary_bot.event
async def on_ready():
    print(f"✅ Primary Bot logged in as {primary_bot.user}")

async def handle_ipc_update(data):
    print(f"Received IPC update: {data}")
    action = data.get("action")
    
    if action == "start_broadcast":
        source_id = int(data.get("source_channel_id"))
        dest_ids = [int(x) for x in data.get("dest_channels", [])]
        
        # 1. Primary bot joins source
        source_channel = primary_bot.get_channel(source_id)
        if not source_channel:
            print(f"Source channel {source_id} not found for primary bot.")
            return
            
        if primary_bot.voice_clients:
            await primary_bot.voice_clients[0].disconnect()
            global_sink.cleanup()
            
        vc = await source_channel.connect()
        vc.start_recording(global_sink, recording_finished_callback)
        print(f"Primary bot started recording in {source_channel.name}")
        
        # 2. Aux bots join destinations
        # Disconnect any currently connected aux bots first
        for b in aux_bots:
            if b.voice_clients:
                await b.voice_clients[0].disconnect()
                
        available_bots = [b for b in aux_bots]
        
        for dest_id in dest_ids:
            if not available_bots:
                print(f"Not enough aux bots to cover channel {dest_id}. Need more tokens!")
                break
            
            aux_bot = available_bots.pop(0)
            dest_channel = aux_bot.get_channel(dest_id)
            
            if dest_channel:
                try:
                    aux_vc = await dest_channel.connect()
                    q = queue.Queue()
                    global_sink.add_subscriber(q)
                    aux_vc.play(BroadcastSource(q))
                    print(f"Aux bot joined {dest_channel.name} and started broadcasting.")
                except Exception as e:
                    print(f"Error connecting aux bot to {dest_id}: {e}")
            else:
                print(f"Destination channel {dest_id} not found for an aux bot. (Is it in the server?)")

    elif action == "stop_broadcast":
        if primary_bot.voice_clients:
            primary_bot.voice_clients[0].stop_recording()
            await primary_bot.voice_clients[0].disconnect()
        global_sink.cleanup()
        
        for b in aux_bots:
            if b.voice_clients:
                b.voice_clients[0].stop()
                await b.voice_clients[0].disconnect()
        print("Broadcast stopped and all bots disconnected.")

async def recording_finished_callback(sink):
    print("Recording finished and sink cleaned up.")

async def main():
    if "your-primary" in settings.DISCORD_PRIMARY_TOKEN:
        print("Please set DISCORD_PRIMARY_TOKEN in .env")
        return

    print("Initializing Database and IPC...")
    await init_db()
    await init_ipc()
    
    loop = asyncio.get_event_loop()
    
    print("Starting IPC listener task...")
    loop.create_task(listen_channel("dab_updates", handle_ipc_update))
    
    # Start primary
    print("Starting Primary Bot...")
    loop.create_task(primary_bot.start(settings.DISCORD_PRIMARY_TOKEN))

    # Start aux bots
    for idx, token in enumerate(aux_tokens):
        if "aux-token" not in token:
            print(f"Starting Aux Bot {idx+1}...")
            loop.create_task(aux_bots[idx].start(token))

    await asyncio.sleep(float('inf'))

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
