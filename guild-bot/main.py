import discord
from discord.ext import commands
from discord import app_commands
import os
import httpx
from dotenv import load_dotenv
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models import DropUser, Build, DropHistory, DropPoll
from datetime import datetime
import json
import urllib.parse

load_dotenv()

TOKEN = os.getenv('GUILD_BOT_TOKEN', '')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'discord_bot')

TEST_GUILD_ID = os.getenv('GUILD_ID', '')

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=discord.Intents.default())

    async def setup_hook(self):
        # Connessione DB
        client = AsyncIOMotorClient(MONGO_URI)
        await init_beanie(database=client[MONGO_DB_NAME], document_models=[DropUser, Build, DropHistory, DropPoll])
        # Sync slash commands
        if TEST_GUILD_ID:
            guild = discord.Object(id=int(TEST_GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"Comandi sincronizzati istantaneamente sul server {TEST_GUILD_ID}")
        else:
            await self.tree.sync()
            print("Comandi sincronizzati globalmente (potrebbe richiedere fino a 1 ora)")
            
        self.add_view(CandidateButton())

bot = MyBot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

# --- Autocomplete Helper ---
async def item_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    if len(current) < 2:
        return []
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "language": "en",
                "page": 1,
                "searchTerm": current
            }
            # Cerca su tutte le categorie omergendo i mainCategory oppure senza specificarlo, assumiamo che questlog funzioni senza.
            # Se la query di questlog richiede mainCategory, iteriamo su un paio o lo chiediamo.
            url = f"https://questlog.gg/throne-and-liberty/api/trpc/database.getItems?input={urllib.parse.quote(json.dumps(payload))}"
            res = await client.get(url)
            if res.status_code == 200:
                data = res.json()
                items = data.get('result', {}).get('data', {}).get('pageData', [])
                choices = []
                allowed_cats = ["weapons", "armor", "accessories"]
                filtered = [item for item in items if item.get('mainCategory', '').lower() in allowed_cats]
                
                for item in filtered[:25]:
                    name_cat = f"{item['name']} ({item['mainCategory']})"[:100]
                    # id + | + name + | + mainCategory
                    val = f"{item['id']}|{item['name']}|{item['mainCategory']}"[:100]
                    choices.append(app_commands.Choice(name=name_cat, value=val))
                return choices
    except Exception as e:
        print(f"Error autocomplete: {e}")
    return []

# --- Views ---
class CandidateButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Candidati per il Drop', style=discord.ButtonStyle.green, custom_id='candidate_btn')
    async def candidate(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Trova sondaggio dal message id
            message_id = str(interaction.message.id)
            poll = await DropPoll.find_one(DropPoll.message_id == message_id)
            if not poll:
                # Fallback per i vecchi sondaggi prima della modifica
                poll = await DropPoll.find_one(DropPoll.channel_id == str(interaction.channel_id), DropPoll.status == "open").sort("-created_at")
                
            if not poll:
                await interaction.response.send_message("Sondaggio non trovato o scaduto.", ephemeral=True)
                return
            
            if poll.status != "open":
                await interaction.response.send_message("Il sondaggio è già chiuso.", ephemeral=True)
                return
                
            discord_id = str(interaction.user.id)
            if discord_id in poll.candidates:
                await interaction.response.send_message("Sei già candidato.", ephemeral=True)
                return

            # Check if user exists
            db_user = await DropUser.find_one(DropUser.discord_id == discord_id)
            if not db_user:
                await interaction.response.send_message("Non sei registrato sul sito. Fai prima il login sulla dashboard.", ephemeral=True)
                return

            # Check if user has primary build in this guild
            guild_id = str(interaction.guild_id)
            build = await Build.find_one(Build.user_id == discord_id, Build.guild_id == guild_id, Build.status == "primary")
            
            if not build:
                await interaction.response.send_message("Non hai una build Primaria approvata per questa gilda.", ephemeral=True)
                return

            # Check if item is in the build
            has_item = False
            if build.slots:
                slots_dict = build.slots.model_dump()
                for slot_key, item_data in slots_dict.items():
                    if item_data and item_data.get("id") == poll.item_id:
                        has_item = True
                        break

            if not has_item:
                await interaction.response.send_message(f"Non puoi candidarti per **{poll.item_name}** perché non è presente nella tua Build Primaria.", ephemeral=True)
                return

            poll.candidates.append(discord_id)
            await poll.save()
            await interaction.response.send_message("Ti sei candidato con successo!", ephemeral=True)
        except Exception as e:
            import traceback
            traceback.print_exc()
            if not interaction.response.is_done():
                await interaction.response.send_message(f"Si è verificato un errore: {e}", ephemeral=True)


# --- Commands ---

@bot.tree.command(name="pinguin_drop_start", description="Avvia un sondaggio per l'assegnazione di un item")
@app_commands.autocomplete(item=item_autocomplete)
async def drop_start(interaction: discord.Interaction, item: str):
    # L'admin invia item che è un json object dumpato
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Solo gli admin possono avviare un drop.", ephemeral=True)
        return
        
    try:
        parts = item.split("|")
        item_data = {"id": parts[0], "name": parts[1] if len(parts) > 1 else parts[0], "category": parts[2] if len(parts) > 2 else "Unknown"}
    except:
        await interaction.response.send_message("Item non valido. Usa l'autocomplete.", ephemeral=True)
        return

    guild_id = str(interaction.guild_id)
    
    poll = DropPoll(
        guild_id=guild_id,
        item_id=item_data["id"],
        item_name=item_data["name"],
        message_id="",
        channel_id=str(interaction.channel_id),
        created_by=str(interaction.user.id)
    )
    await poll.save()

    # Try to fetch item icon
    icon_url = None
    try:
        import urllib.parse
        payload = {"searchTerm": item_data["name"], "language": "en", "page": 1}
        url = f"https://questlog.gg/throne-and-liberty/api/trpc/database.getItems?input={urllib.parse.quote(json.dumps(payload))}"
        async with httpx.AsyncClient() as client:
            res = await client.get(url)
            if res.status_code == 200:
                data = res.json()
                items = data.get('result', {}).get('data', {}).get('pageData', [])
                for i in items:
                    if i.get('id') == item_data['id']:
                        raw_icon = i.get('icon', '')
                        if raw_icon:
                            if not raw_icon.startswith("/"):
                                raw_icon = "/" + raw_icon
                            icon_url = "https://cdn.questlog.gg/throne-and-liberty" + raw_icon.split('.')[0] + ".webp"
                        break
    except Exception as e:
        print(f"Error fetching icon: {e}")

    view = CandidateButton()
    
    embed = discord.Embed(
        title="🎉 Nuovo Drop Assegnabile!",
        description=f"Item: **{item_data['name']}**\nClicca sul bottone per candidarti se hai questo pezzo nella tua build *Primary*.",
        color=discord.Color.gold()
    )
    if icon_url:
        embed.set_thumbnail(url=icon_url)
    
    await interaction.response.send_message(embed=embed, view=view)
    msg = await interaction.original_response()
    poll.message_id = str(msg.id)
    await poll.save()

# @bot.tree.command(name="pinguin_drop_cancel", description="Annulla il sondaggio attivo in questo canale senza assegnare il drop")
# async def drop_cancel(interaction: discord.Interaction):
#     if not interaction.user.guild_permissions.administrator:
#         await interaction.response.send_message("Solo gli admin possono annullare un drop.", ephemeral=True)
#         return
#
#     guild_id = str(interaction.guild_id)
#     channel_id = str(interaction.channel_id)
#
#     # Prendi l'ultimo sondaggio aperto del server in questo canale
#     poll = await DropPoll.find_one(DropPoll.guild_id == guild_id, DropPoll.channel_id == channel_id, DropPoll.status == "open").sort("-created_at")
#
#     if not poll:
#         await interaction.response.send_message("Nessun drop attivo trovato in questo canale.", ephemeral=True)
#         return
#
#     poll.status = "canceled"
#     await poll.save()
#
#     # Rimuovi i bottoni dal messaggio originale
#     if poll.message_id:
#         try:
#             msg = await interaction.channel.fetch_message(int(poll.message_id))
#             await msg.edit(view=None)
#         except Exception as e:
#             print(f"Non sono riuscito a rimuovere il view dal messaggio originale: {e}")
#             pass
#
#     embed = discord.Embed(
#         title="🛑 Drop Annullato",
#         description=f"Il sondaggio per **{poll.item_name}** è stato annullato da {interaction.user.mention} senza assegnazioni.",
#         color=discord.Color.red()
#     )
#
#     await interaction.response.send_message(embed=embed)

# drop_close e drop_assign rimossi, gestiti via Web UI

if __name__ == '__main__':
    bot.run(TOKEN)
