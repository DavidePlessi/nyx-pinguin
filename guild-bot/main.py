import discord
from discord.ext import commands
from discord import app_commands
import os
import httpx
from dotenv import load_dotenv
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models import DropUser, Build, DropHistory, DropPoll, GuildConfig, AvailableLanguage, SkillCore, WeeklyGameActivity, BotLog
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
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        # Connessione DB
        client = AsyncIOMotorClient(MONGO_URI)
        await init_beanie(database=client[MONGO_DB_NAME], document_models=[DropUser, Build, DropHistory, DropPoll, GuildConfig, AvailableLanguage, WeeklyGameActivity, BotLog, SkillCore])
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
        self.add_view(LucentCandidateButton())

        # Load cogs
        await self.load_extension('cogs.weekly_activity')

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

async def skillcore_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    if len(current) < 2:
        return []
    try:
        cores = await SkillCore.find({"name": {"$regex": current, "$options": "i"}}).limit(25).to_list()
        choices = []
        for c in cores:
            val = f"{str(c.id)}|{c.name}|{c.slot}"[:100]
            display = f"{c.name} [{c.slot}]"[:100]
            choices.append(app_commands.Choice(name=display, value=val))
        return choices
    except Exception as e:
        print(f"Error skillcore autocomplete: {e}")
    return []

# --- Views ---
async def update_poll_message(interaction: discord.Interaction, poll: DropPoll):
    try:
        msg = interaction.message
        if not msg:
            channel = interaction.client.get_channel(int(poll.channel_id))
            if not channel:
                channel = await interaction.client.fetch_channel(int(poll.channel_id))
            msg = await channel.fetch_message(int(poll.message_id))
            
        if not msg or not msg.embeds: return
        embed = msg.embeds[0]
        embed.clear_fields()
        
        if poll.candidates:
            if poll.poll_type == 'lucent':
                embed.add_field(name="Participants", value=f"Total Candidates: {len(poll.candidates)}", inline=False)
            else:
                grouped = {}
                for uid, reason in poll.candidate_reasons.items():
                    if reason not in grouped:
                        grouped[reason] = []
                    grouped[reason].append(f"<@{uid}>")
                
                text = ""
                for reason, users in grouped.items():
                    text += f"**{reason}** ({len(users)}):\n" + ", ".join(users) + "\n\n"
                
                embed.add_field(name="Participants", value=text[:1024], inline=False)
        
        await msg.edit(embed=embed)
    except Exception as e:
        print(f"Error updating poll message: {e}")

class CandidateButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def process_candidate(self, interaction: discord.Interaction, reason: str):
        try:
            # Trova sondaggio dal message id
            message_id = str(interaction.message.id)
            poll = await DropPoll.find_one(DropPoll.message_id == message_id)
            if not poll:
                # Fallback per i vecchi sondaggi prima della modifica
                poll = await DropPoll.find_one(DropPoll.channel_id == str(interaction.channel_id), DropPoll.status == "open").sort("-created_at")
                
            if not poll:
                await interaction.response.send_message("Poll not found or expired.", ephemeral=True)
                return
            
            if poll.status != "open":
                await interaction.response.send_message("The poll is already closed.", ephemeral=True)
                return
                
            discord_id = str(interaction.user.id)
            if discord_id in poll.candidates:
                await interaction.response.send_message("You are already a candidate.", ephemeral=True)
                return

            # Check if user exists
            db_user = await DropUser.find_one(DropUser.discord_id == discord_id)
            if not db_user:
                await interaction.response.send_message("You are not registered on the site. Please login to the dashboard first.", ephemeral=True)
                return

            guild_id = str(interaction.guild_id)
            guild_config = await GuildConfig.find_one(GuildConfig.guild_id == guild_id)
            strict_check = guild_config.drop_strict_primary if guild_config else True

            # Per "Build Primaria" controlliamo rigorosamente se l'ha salvata
            if reason == "Primary Build" and strict_check:
                build = await Build.find_one(Build.user_id == discord_id, Build.guild_id == guild_id, Build.status == "primary")
                
                if not build:
                    await interaction.response.send_message("You don't have an approved Primary build for this guild.", ephemeral=True)
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
                    import urllib.parse
                    import json
                    import httpx
                    
                    try:
                        url = f"https://questlog.gg/throne-and-liberty/api/trpc/database.getItem?input={urllib.parse.quote(json.dumps({'id': poll.item_id, 'language': 'en'}))}"
                        async with httpx.AsyncClient() as client:
                            res = await client.get(url)
                            if res.status_code == 200:
                                data = res.json()
                                item_info = data.get('result', {}).get('data', {})
                                perks = item_info.get('itemConvertsToPerks', [])
                                if perks:
                                    for perk in perks:
                                        perk_name = perk.get('name', '')
                                        clean_perk_name = perk_name.replace("Skill Core: ", "").strip()
                                        
                                        if build.skillcores:
                                            sc_dict = build.skillcores.model_dump()
                                            for sc_key, sc_data in sc_dict.items():
                                                if sc_data and sc_data.get("name"):
                                                    sc_name = sc_data.get("name")
                                                    clean_sc_name = sc_name.replace("Skill Core: ", "").strip()
                                                    if clean_sc_name == clean_perk_name or sc_name == perk_name:
                                                        has_item = True
                                                        break
                                        if has_item:
                                            break
                    except Exception as e:
                        print(f"Error checking skillcore fallback: {e}")

                if not has_item:
                    await interaction.response.send_message(f"You cannot apply for **{poll.item_name}** because it is not present in your Primary Build.", ephemeral=True)
                    return

            poll.candidates.append(discord_id)
            if not getattr(poll, "candidate_reasons", None):
                poll.candidate_reasons = {}
            poll.candidate_reasons[discord_id] = reason
            await poll.save()
            await update_poll_message(interaction, poll)
            await interaction.response.send_message(f"You successfully applied for: **{reason}**!", ephemeral=True)
        except Exception as e:
            import traceback
            traceback.print_exc()
            if not interaction.response.is_done():
                await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

    @discord.ui.button(label='Primary Build', style=discord.ButtonStyle.green, custom_id='candidate_primary_btn')
    async def candidate_primary(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_candidate(interaction, "Primary Build")

    @discord.ui.button(label='Water-Lito', style=discord.ButtonStyle.blurple, custom_id='candidate_litograph_btn')
    async def candidate_litograph(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_candidate(interaction, "Water-Lito")

    @discord.ui.button(label='Secondary Build', style=discord.ButtonStyle.gray, custom_id='candidate_secondary_btn')
    async def candidate_secondary(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_candidate(interaction, "Secondary Build")


class SkillcoreCandidateButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def process_candidate(self, interaction: discord.Interaction, reason: str):
        try:
            # Trova sondaggio dal message id
            message_id = str(interaction.message.id)
            poll = await DropPoll.find_one(DropPoll.message_id == message_id)
            if not poll:
                poll = await DropPoll.find_one(DropPoll.channel_id == str(interaction.channel_id), DropPoll.status == "open").sort("-created_at")
                
            if not poll:
                await interaction.response.send_message("Poll not found or expired.", ephemeral=True)
                return
            
            if poll.status != "open":
                await interaction.response.send_message("The poll is already closed.", ephemeral=True)
                return
                
            discord_id = str(interaction.user.id)
            if discord_id in poll.candidates:
                await interaction.response.send_message("You are already a candidate.", ephemeral=True)
                return

            db_user = await DropUser.find_one(DropUser.discord_id == discord_id)
            if not db_user:
                await interaction.response.send_message("You are not registered on the site. Please login to the dashboard first.", ephemeral=True)
                return

            guild_id = str(interaction.guild_id)
            guild_config = await GuildConfig.find_one(GuildConfig.guild_id == guild_id)
            strict_check = guild_config.drop_strict_primary if guild_config else True

            if reason == "Primary Build" and strict_check:
                build = await Build.find_one(Build.user_id == discord_id, Build.guild_id == guild_id, Build.status == "primary")
                
                if not build:
                    await interaction.response.send_message("You don't have an approved Primary build for this guild.", ephemeral=True)
                    return

                has_item = False
                if build.skillcores:
                    sc_dict = build.skillcores.model_dump()
                    for slot_key, item_data in sc_dict.items():
                        if item_data and item_data.get("id") == poll.item_id:
                            has_item = True
                            break

                if not has_item:
                    await interaction.response.send_message(f"You cannot apply for **{poll.item_name}** because it is not present in your Primary Build.", ephemeral=True)
                    return

            poll.candidates.append(discord_id)
            if not getattr(poll, "candidate_reasons", None):
                poll.candidate_reasons = {}
            poll.candidate_reasons[discord_id] = reason
            await poll.save()
            await update_poll_message(interaction, poll)
            await interaction.response.send_message(f"You successfully applied for: **{reason}**!", ephemeral=True)
        except Exception as e:
            import traceback
            traceback.print_exc()
            if not interaction.response.is_done():
                await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

    @discord.ui.button(label='Primary Build', style=discord.ButtonStyle.green, custom_id='candidate_skillcore_primary_btn')
    async def candidate_primary(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_candidate(interaction, "Primary Build")

    @discord.ui.button(label='Secondary Build', style=discord.ButtonStyle.gray, custom_id='candidate_skillcore_secondary_btn')
    async def candidate_secondary(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_candidate(interaction, "Secondary Build")

    @discord.ui.button(label='Dissolve', style=discord.ButtonStyle.red, custom_id='candidate_skillcore_dissolve_btn')
    async def candidate_dissolve(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_candidate(interaction, "Dissolve")



class LucentModal(discord.ui.Modal, title='Lucent Application'):
    amount = discord.ui.TextInput(
        label='Requested amount',
        style=discord.TextStyle.short,
        placeholder='E.g. 500',
        required=True
    )
    reason = discord.ui.TextInput(
        label='Note / Reason',
        style=discord.TextStyle.paragraph,
        placeholder='Why are you requesting these lucent?',
        required=True,
        max_length=300
    )

    def __init__(self, target_message_id: str, target_channel_id: str):
        super().__init__()
        self.target_message_id = target_message_id
        self.target_channel_id = target_channel_id

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Trova sondaggio dal message id salvato
            poll = await DropPoll.find_one(DropPoll.message_id == self.target_message_id)
            if not poll:
                poll = await DropPoll.find_one(DropPoll.channel_id == self.target_channel_id, DropPoll.status == "open").sort("-created_at")
                
            if not poll:
                await interaction.response.send_message("Poll not found or expired.", ephemeral=True)
                return
            
            if poll.status != "open":
                await interaction.response.send_message("The poll is already closed.", ephemeral=True)
                return
                
            discord_id = str(interaction.user.id)
            if discord_id in poll.candidates:
                await interaction.response.send_message("You are already a candidate.", ephemeral=True)
                return

            db_user = await DropUser.find_one(DropUser.discord_id == discord_id)
            if not db_user:
                await interaction.response.send_message("You are not registered on the site. Please login to the dashboard first.", ephemeral=True)
                return

            try:
                amt = int(self.amount.value)
            except ValueError:
                await interaction.response.send_message("The amount must be an integer.", ephemeral=True)
                return

            poll.candidates.append(discord_id)
            if getattr(poll, "candidate_reasons", None) is None:
                poll.candidate_reasons = {}
            if getattr(poll, "candidate_amounts", None) is None:
                poll.candidate_amounts = {}
            poll.candidate_reasons[discord_id] = self.reason.value
            poll.candidate_amounts[discord_id] = amt
            await poll.save()
            await update_poll_message(interaction, poll)
            await interaction.response.send_message(f"You successfully applied for {amt} Lucent!", ephemeral=True)
        except Exception as e:
            import traceback
            traceback.print_exc()
            if not interaction.response.is_done():
                await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

class LucentCandidateButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Apply for Lucent', style=discord.ButtonStyle.green, custom_id='candidate_lucent_btn')
    async def candidate_lucent(self, interaction: discord.Interaction, button: discord.ui.Button):
        msg_id = str(interaction.message.id) if interaction.message else ""
        chan_id = str(interaction.channel_id) if interaction.channel_id else ""
        await interaction.response.send_modal(LucentModal(target_message_id=msg_id, target_channel_id=chan_id))

# --- Commands ---

# --- Translate Context Menu & Reactions ---

from translators import translate_mymemory, translate_deepl, translate_gemini

async def perform_translation(text: str, target_lang: str, config) -> str:
    service = getattr(config, "translation_service", "mymemory")
    if service == "deepl":
        return await translate_deepl(text, target_lang)
    elif service == "gemini":
        return await translate_gemini(text, target_lang)
    else:
        return await translate_mymemory(text, target_lang)

class TranslateView(discord.ui.View):
    def __init__(self, message: discord.Message, options: list[discord.SelectOption], mode: str, config):
        super().__init__(timeout=120)
        self.message = message
        self.mode = mode
        self.config = config
        
        self.select = discord.ui.Select(placeholder="Scegli la lingua...", options=options[:25])
        self.select.callback = self.select_callback
        self.add_item(self.select)
        
    async def select_callback(self, interaction: discord.Interaction):
        # The value is stored as 'langCode_emojiName' to prevent Discord duplicate value errors
        lang_val = self.select.values[0]
        lang_code = lang_val.split('_')[0]
        lang_name = next(opt.label for opt in self.select.options if opt.value == lang_val)
        
        await interaction.response.defer(ephemeral=(self.mode == "ephemeral"))
        
        try:
            translated = await perform_translation(self.message.content, lang_code, self.config)
            
            embed = discord.Embed(
                description=translated,
                color=discord.Color.blue()
            )
            
            author_icon = self.message.author.display_avatar.url if self.message.author.display_avatar else None
            embed.set_author(name=f"Messaggio originale di {self.message.author.display_name}", icon_url=author_icon)
            
            requester_name = interaction.user.display_name
            embed.set_footer(text=f"Traduzione in {lang_name} richiesta da {requester_name}")
            
            if self.mode == "ephemeral":
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                # Find the emoji for the selected language
                selected_emoji = next((opt.emoji.name for opt in self.select.options if opt.value == lang_val and opt.emoji), "✅")
                
                # To prevent spam in channel mode, check if we already translated it
                if not any(reaction.me and str(reaction.emoji) == selected_emoji for reaction in self.message.reactions):
                    try:
                        await self.message.add_reaction(selected_emoji)
                    except:
                        pass
                    await self.message.reply(embed=embed, mention_author=False)
                    await interaction.followup.send("Messaggio tradotto nel canale.", ephemeral=True)
                else:
                    await interaction.followup.send("Il messaggio è già stato tradotto in questa lingua nel canale.", ephemeral=True)
                
        except Exception as e:
            print(f"Errore traduzione: {e}")
            await interaction.followup.send(f"⚠️ Impossibile tradurre il messaggio al momento. Riprova più tardi.", ephemeral=True)

@bot.tree.context_menu(name="Traduci")
async def translate_message_context(interaction: discord.Interaction, message: discord.Message):
    if not message.content:
        await interaction.response.send_message("Il messaggio è vuoto.", ephemeral=True)
        return

    guild_id = str(interaction.guild_id)
    config = await GuildConfig.find_one(GuildConfig.guild_id == guild_id)
    
    if not config or not config.is_active:
        await interaction.response.send_message("Configurazione bot non attiva in questo server.", ephemeral=True)
        return
    
    if not config.translation_ephemeral:
        await interaction.response.send_message("La traduzione tramite menù contestuale (effimera) è disabilitata in questo server. Usa le reazioni con le bandiere se la traduzione nel canale è attiva.", ephemeral=True)
        return

    enabled_langs_codes = config.translation_languages
    if not enabled_langs_codes:
        await interaction.response.send_message("Nessuna lingua abilitata per la traduzione in questo server.", ephemeral=True)
        return
        
    all_langs = await AvailableLanguage.find_all().to_list()
    if not all_langs:
        # Fallback if DB empty
        all_langs = [AvailableLanguage(code="en", name="Inglese", emoji="🇬🇧"), AvailableLanguage(code="it", name="Italiano", emoji="🇮🇹")]
    
    options = []
    for lang in all_langs:
        if lang.code in enabled_langs_codes:
            unique_val = f"{lang.code}_{lang.emoji}"
            options.append(discord.SelectOption(label=lang.name, value=unique_val, emoji=lang.emoji))
            
    if not options:
        await interaction.response.send_message("Nessuna lingua valida abilitata.", ephemeral=True)
        return

    view = TranslateView(message, options, "ephemeral", config)
    await interaction.response.send_message("Seleziona la lingua per la traduzione:", view=view, ephemeral=True)

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.user_id == bot.user.id:
        return

    emoji_name = str(payload.emoji)
    
    config = await GuildConfig.find_one(GuildConfig.guild_id == str(payload.guild_id))
    if not config or not config.is_active:
        return
    
    # Check if the reaction emoji is an enabled language
    all_langs = await AvailableLanguage.find_all().to_list()
    target_lang = None
    for lang in all_langs:
        if lang.emoji == emoji_name and lang.code in config.translation_languages:
            target_lang = lang
            break
            
    if not target_lang:
        return
        
    lang_code = target_lang.code
    lang_name = target_lang.name

    print(f"[Traduzioni] Ricevuta richiesta di traduzione (Reazione) in {lang_name} sul server {payload.guild_id}")
    
    channel = bot.get_channel(payload.channel_id)
    if not channel:
        try:
            channel = await bot.fetch_channel(payload.channel_id)
        except Exception as e:
            print(f"[Traduzioni] Impossibile recuperare il canale: {e}")
            return

    try:
        message = await channel.fetch_message(payload.message_id)
    except Exception:
        return

    if not message.content:
        return

    if not config.translation_channel:
        # Avvisa l'utente se prova a usare la reazione ma la modalità è disabilitata
        user = bot.get_user(payload.user_id)
        if user:
            try:
                await user.send(f"⚠️ La traduzione nel canale tramite reazioni è disabilitata nel server. Usa il menù contestuale (Tasto destro sul messaggio -> App -> Traduci) se la traduzione effimera è attiva.")
            except:
                pass
        
        # Rimuove la reazione
        channel = bot.get_channel(payload.channel_id)
        if channel:
            try:
                message = await channel.fetch_message(payload.message_id)
                await message.remove_reaction(payload.emoji, user)
            except:
                pass
        return

    for reaction in message.reactions:
        if str(reaction.emoji) == emoji_name and reaction.me:
            return

    try:
        await message.add_reaction(payload.emoji)
    except:
        pass

    try:
        translated = await perform_translation(message.content, lang_code, config)
        
        embed = discord.Embed(
            description=translated,
            color=discord.Color.blue()
        )
        author_icon = message.author.display_avatar.url if message.author.display_avatar else None
        embed.set_author(name=f"Messaggio originale di {message.author.display_name}", icon_url=author_icon)
        requester_name = payload.member.display_name if payload.member else "Utente"
        embed.set_footer(text=f"Traduzione in {lang_name} richiesta da {requester_name}")
        
        await message.reply(embed=embed, mention_author=False)
    except Exception as e:
        print(f"Errore traduzione: {e}")
        try:
            await message.remove_reaction(payload.emoji, bot.user)
        except:
            pass
        try:
            requester_mention = payload.member.mention if payload.member else "Utente"
            await channel.send(f"{requester_mention}, ⚠️ Impossibile tradurre il messaggio in {lang_name} al momento. Riprova più tardi.", delete_after=15)
        except:
            pass

@bot.tree.command(name="pinguin_drop_start", description="Start a poll for item assignment")
@app_commands.autocomplete(item=item_autocomplete)
async def drop_start(interaction: discord.Interaction, item: str):
    # L'admin invia item che è un json object dumpato
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Only admins can start a drop.", ephemeral=True)
        return
        
    try:
        parts = item.split("|")
        item_data = {"id": parts[0], "name": parts[1] if len(parts) > 1 else parts[0], "category": parts[2] if len(parts) > 2 else "Unknown"}
    except:
        await interaction.response.send_message("Invalid item. Use autocomplete.", ephemeral=True)
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
        title="🎉 New Drop Available!",
        description=f"Item: **{item_data['name']}**\nChoose the reason for your candidacy using the buttons below.\n\n🌐 [View Active Polls & Drop History](https://nyx-pinguin.fiveamtech.it/guild-drops)",
        color=discord.Color.gold()
    )
    if icon_url:
        embed.set_thumbnail(url=icon_url)
    
    await interaction.response.send_message(embed=embed, view=view)
    msg = await interaction.original_response()
    poll.message_id = str(msg.id)
    await poll.save()


@bot.tree.command(name="pinguin_skillcore_start", description="Start a poll for a skillcore assignment")
@app_commands.autocomplete(skillcore=skillcore_autocomplete)
async def skillcore_start(interaction: discord.Interaction, skillcore: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Only admins can start a drop.", ephemeral=True)
        return
        
    try:
        parts = skillcore.split("|")
        item_data = {"id": parts[0], "name": parts[1] if len(parts) > 1 else parts[0], "category": parts[2] if len(parts) > 2 else "Unknown"}
    except:
        await interaction.response.send_message("Invalid skillcore. Use autocomplete.", ephemeral=True)
        return

    # Check if skillcore exists in DB to get the image
    from bson import ObjectId
    try:
        core = await SkillCore.get(ObjectId(item_data["id"]))
        icon_url = core.imageUrl if core else None
    except:
        icon_url = None

    guild_id = str(interaction.guild_id)
    
    poll = DropPoll(
        guild_id=guild_id,
        item_id=item_data["id"],
        item_name=item_data["name"],
        message_id="",
        channel_id=str(interaction.channel_id),
        poll_type="skillcore",
        created_by=str(interaction.user.id)
    )
    await poll.save()

    view = SkillcoreCandidateButton()
    
    embed = discord.Embed(
        title="🎉 New Skillcore Drop Available!",
        description=f"Skillcore: **{item_data['name']}**\nChoose the reason for your candidacy using the buttons below.\n\n🌐 [View Active Polls & Drop History](https://nyx-pinguin.fiveamtech.it/guild-drops)",
        color=discord.Color.purple()
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


@bot.tree.command(name="pinguin_lucent_start", description="Start a poll for Lucent assignment")
@app_commands.describe(amount="Total amount of Lucent to assign")
async def lucent_start(interaction: discord.Interaction, amount: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Only admins can start a Lucent poll.", ephemeral=True)
        return

    guild_id = str(interaction.guild_id)
    
    poll = DropPoll(
        guild_id=guild_id,
        item_id="lucent",
        item_name="Lucent",
        message_id="",
        channel_id=str(interaction.channel_id),
        poll_type="lucent",
        amount=amount,
        created_by=str(interaction.user.id)
    )
    await poll.save()

    view = LucentCandidateButton()
    
    embed = discord.Embed(
        title="💰 Lucent Assignment!",
        description=f"Amount available: **{amount} Lucent**\nClick the button below to enter the requested amount and reason.\n\n🌐 [View Active Polls & Drop History](https://nyx-pinguin.fiveamtech.it/guild-drops)",
        color=discord.Color.gold()
    )
    
    await interaction.response.send_message(embed=embed, view=view)
    msg = await interaction.original_response()
    poll.message_id = str(msg.id)
    await poll.save()

if __name__ == '__main__':
    bot.run(TOKEN)
