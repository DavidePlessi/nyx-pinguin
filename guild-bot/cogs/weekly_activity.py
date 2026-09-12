import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
from models import GuildConfig, WeeklyGameActivity, BotLog

LOCALES = {
    "en": {
        "title": "📊 Weekly Activity Log",
        "desc": "{role_mention} It's time to log your weekly in-game activity!\n\nPlease click the button below to submit your score for **{week_id}**.",
        "btn": "Log Activity",
        "rem_title": "⚠️ Weekly Activity Reminder",
        "rem_desc": "The following members still need to log their activity for **{week_id}**:\n\n{slackers}\n\nPlease click the button below to log your score before the cutoff!",
        "mod_title": "Log Weekly Activity",
        "mod_lbl": "Activity Score",
        "mod_ph": "e.g. 5500",
        "err_num": "Please enter a valid number.",
        "err_dis": "Weekly activity tracking is not enabled for this server.",
        "err_neg": "Score cannot be negative.",
        "succ_upd": "Your activity score for {week_id} has been updated to **{score}**!",
        "succ_log": "Your activity score of **{score}** has been logged for {week_id}. Thank you!"
    },
    "it": {
        "title": "📊 Log Attività Settimanale",
        "desc": "{role_mention} È il momento di registrare la tua attività settimanale!\n\nClicca il pulsante qui sotto per inviare il tuo punteggio per **{week_id}**.",
        "btn": "Registra Attività",
        "rem_title": "⚠️ Promemoria Attività Settimanale",
        "rem_desc": "I seguenti membri devono ancora registrare la loro attività per **{week_id}**:\n\n{slackers}\n\nClicca il pulsante qui sotto per inviare il tuo punteggio prima della scadenza!",
        "mod_title": "Registra Attività",
        "mod_lbl": "Punteggio Attività",
        "mod_ph": "es. 5500",
        "err_num": "Inserisci un numero valido.",
        "err_dis": "Il tracciamento dell'attività non è abilitato per questo server.",
        "err_neg": "Il punteggio non può essere negativo.",
        "succ_upd": "Il tuo punteggio per {week_id} è stato aggiornato a **{score}**!",
        "succ_log": "Il tuo punteggio di **{score}** è stato registrato per {week_id}. Grazie!"
    },
    "fr": {
        "title": "📊 Journal d'Activité Hebdomadaire",
        "desc": "{role_mention} Il est temps d'enregistrer votre activité hebdomadaire!\n\nVeuillez cliquer sur le bouton ci-dessous pour soumettre votre score pour **{week_id}**.",
        "btn": "Enregistrer l'activité",
        "rem_title": "⚠️ Rappel d'Activité Hebdomadaire",
        "rem_desc": "Les membres suivants doivent encore enregistrer leur activité pour **{week_id}**:\n\n{slackers}\n\nVeuillez cliquer sur le bouton ci-dessous pour soumettre votre score avant la date limite!",
        "mod_title": "Enregistrer l'Activité",
        "mod_lbl": "Score d'Activité",
        "mod_ph": "ex. 5500",
        "err_num": "Veuillez entrer un nombre valide.",
        "err_dis": "Le suivi d'activité n'est pas activé pour ce serveur.",
        "err_neg": "Le score ne peut pas être négatif.",
        "succ_upd": "Votre score d'activité pour {week_id} a été mis à jour à **{score}**!",
        "succ_log": "Votre score d'activité de **{score}** a été enregistré pour {week_id}. Merci!"
    },
    "es": {
        "title": "📊 Registro de Actividad Semanal",
        "desc": "{role_mention} ¡Es hora de registrar tu actividad semanal!\n\nHaz clic en el botón de abajo para enviar tu puntuación de **{week_id}**.",
        "btn": "Registrar Actividad",
        "rem_title": "⚠️ Recordatorio de Actividad Semanal",
        "rem_desc": "Los siguientes miembros aún necesitan registrar su actividad para **{week_id}**:\n\n{slackers}\n\n¡Haz clic en el botón de abajo para registrar tu puntuación antes del cierre!",
        "mod_title": "Registrar Actividad",
        "mod_lbl": "Puntuación de Actividad",
        "mod_ph": "ej. 5500",
        "err_num": "Por favor, ingresa un número válido.",
        "err_dis": "El seguimiento de actividad no está habilitado para este servidor.",
        "err_neg": "La puntuación no puede ser negativa.",
        "succ_upd": "¡Tu puntuación de actividad para {week_id} se ha actualizado a **{score}**!",
        "succ_log": "¡Tu puntuación de actividad de **{score}** se ha registrado para {week_id}. Gracias!"
    },
    "de": {
        "title": "📊 Wöchentliches Aktivitätsprotokoll",
        "desc": "{role_mention} Es ist Zeit, deine wöchentliche Aktivität einzutragen!\n\nBitte klicke auf den Button unten, um deine Punktzahl für **{week_id}** zu übermitteln.",
        "btn": "Aktivität eintragen",
        "rem_title": "⚠️ Wöchentliche Aktivität Erinnerung",
        "rem_desc": "Die folgenden Mitglieder müssen ihre Aktivität für **{week_id}** noch eintragen:\n\n{slackers}\n\nBitte klicke auf den Button unten, um deine Punktzahl vor dem Stichtag einzutragen!",
        "mod_title": "Aktivität eintragen",
        "mod_lbl": "Aktivitätspunktzahl",
        "mod_ph": "z.B. 5500",
        "err_num": "Bitte gib eine gültige Zahl ein.",
        "err_dis": "Die Aktivitätsverfolgung ist für diesen Server nicht aktiviert.",
        "err_neg": "Die Punktzahl darf nicht negativ sein.",
        "succ_upd": "Deine Aktivitätspunktzahl für {week_id} wurde auf **{score}** aktualisiert!",
        "succ_log": "Deine Aktivitätspunktzahl von **{score}** wurde für {week_id} eingetragen. Danke!"
    }
}

class LogActivityModal(discord.ui.Modal):
    def __init__(self, t: dict):
        super().__init__(title=t["mod_title"])
        self.t = t
        self.score_input = discord.ui.TextInput(
            label=t["mod_lbl"],
            style=discord.TextStyle.short,
            placeholder=t["mod_ph"],
            required=True,
            custom_id="score_input"
        )
        self.add_item(self.score_input)

    def get_current_week_id(self):
        now = datetime.utcnow()
        year, week, _ = now.isocalendar()
        return f"{year}-W{week:02d}"

    async def on_submit(self, interaction: discord.Interaction):
        try:
            score_val = int(self.score_input.value)
        except ValueError:
            await interaction.response.send_message(self.t["err_num"], ephemeral=True)
            return

        guild_id = str(interaction.guild_id)
        config = await GuildConfig.find_one(GuildConfig.guild_id == guild_id)
        
        if not config or not getattr(config, "weekly_activity_enabled", False):
            await interaction.response.send_message(self.t["err_dis"], ephemeral=True)
            return
            
        if score_val < 0:
            await interaction.response.send_message(self.t["err_neg"], ephemeral=True)
            return

        week_id = self.get_current_week_id()
        player_id = str(interaction.user.id)
        player_name = interaction.user.display_name
        
        existing = await WeeklyGameActivity.find_one(
            WeeklyGameActivity.guild_id == guild_id,
            WeeklyGameActivity.player_id == player_id,
            WeeklyGameActivity.week_id == week_id
        )
        
        if existing:
            existing.activity_score = score_val
            existing.reported_at = datetime.utcnow()
            await existing.save()
            msg = self.t["succ_upd"].replace("{week_id}", week_id).replace("{score}", str(score_val))
            await interaction.response.send_message(msg, ephemeral=True)
        else:
            new_entry = WeeklyGameActivity(
                guild_id=guild_id,
                player_id=player_id,
                player_name=player_name,
                week_id=week_id,
                activity_score=score_val
            )
            await new_entry.save()
            msg = self.t["succ_log"].replace("{week_id}", week_id).replace("{score}", str(score_val))
            await interaction.response.send_message(msg, ephemeral=True)


class LogActivityView(discord.ui.View):
    def __init__(self, t: dict = None):
        super().__init__(timeout=None)
        # If instantiated globally for persistent catch, button label defaults to English but doesn't matter
        btn_label = t["btn"] if t else "Log Activity"
        
        # We must create the button dynamically to translate its label before sending to channel
        self.btn = discord.ui.Button(label=btn_label, style=discord.ButtonStyle.primary, custom_id="log_activity_btn", emoji="📝")
        self.btn.callback = self.log_activity_button
        self.add_item(self.btn)

    async def log_activity_button(self, interaction: discord.Interaction):
        # We look up language dynamically when clicked!
        guild_id = str(interaction.guild_id)
        config = await GuildConfig.find_one(GuildConfig.guild_id == guild_id)
        lang = getattr(config, "bot_language", "en") if config else "en"
        t = LOCALES.get(lang, LOCALES["en"])
        await interaction.response.send_modal(LogActivityModal(t))


class WeeklyActivity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(LogActivityView())
        self.weekly_activity_loop.start()

    def cog_unload(self):
        self.weekly_activity_loop.cancel()
        
    def get_current_week_id(self):
        now = datetime.utcnow()
        year, week, _ = now.isocalendar()
        return f"{year}-W{week:02d}"

    @tasks.loop(minutes=1)
    async def weekly_activity_loop(self):
        now = datetime.utcnow()
        current_day = now.weekday() # 0 = Monday, 6 = Sunday
        current_time_str = now.strftime("%H:%M")
        week_id = self.get_current_week_id()
        
        configs = await GuildConfig.find(GuildConfig.weekly_activity_enabled == True).to_list()
        
        for config in configs:
            # Check if today is the correct day
            if getattr(config, "weekly_activity_day", -1) != current_day:
                continue
                
            channel_id = getattr(config, "weekly_activity_channel_id", None)
            if not channel_id:
                continue
                
            lang = getattr(config, "bot_language", "en")
            t = LOCALES.get(lang, LOCALES["en"])
                
            # Announce time
            if current_time_str == getattr(config, "weekly_activity_announce_time", ""):
                try:
                    channel = self.bot.get_channel(int(channel_id))
                    if channel:
                        role_mention = f"<@&{config.member_role_id}>" if getattr(config, "member_role_id", None) else ""
                        desc = t["desc"].replace("{role_mention}", role_mention).replace("{week_id}", week_id)
                        embed = discord.Embed(
                            title=t["title"],
                            description=desc,
                            color=discord.Color.blue()
                        )
                        await channel.send(embed=embed, view=LogActivityView(t))
                        await BotLog(level="info", message=f"Sent weekly activity announcement for guild {config.guild_id} (Week {week_id}).").save()
                except Exception as e:
                    await BotLog(level="error", message=f"Failed to send weekly announcement for guild {config.guild_id}: {e}").save()
            
            # Reminder time
            elif current_time_str == getattr(config, "weekly_activity_reminder_time", ""):
                try:
                    guild = self.bot.get_guild(int(config.guild_id))
                    channel = self.bot.get_channel(int(channel_id))
                    if not guild or not channel:
                        continue
                        
                    role_id = getattr(config, "member_role_id", None)
                    if not role_id:
                        continue
                        
                    role = guild.get_role(int(role_id))
                    if not role:
                        continue
                    
                    # Get all members with role
                    members_with_role = role.members
                    if not members_with_role:
                        continue
                        
                    # Find who already submitted
                    submissions = await WeeklyGameActivity.find(
                        WeeklyGameActivity.guild_id == config.guild_id,
                        WeeklyGameActivity.week_id == week_id
                    ).to_list()
                    
                    submitted_ids = {sub.player_id for sub in submissions}
                    
                    # Ping slackers
                    slackers = [m for m in members_with_role if str(m.id) not in submitted_ids and not m.bot]
                    if slackers:
                        slacker_mentions = " ".join([m.mention for m in slackers])
                        desc = t["rem_desc"].replace("{slackers}", slacker_mentions).replace("{week_id}", week_id)
                        embed = discord.Embed(
                            title=t["rem_title"],
                            description=desc,
                            color=discord.Color.red()
                        )
                        await channel.send(embed=embed, view=LogActivityView(t))
                        await BotLog(level="info", message=f"Sent weekly activity reminder for guild {config.guild_id}. Slackers: {len(slackers)}").save()
                    else:
                        await BotLog(level="info", message=f"Weekly activity reminder skipped for guild {config.guild_id}: No slackers!").save()
                except Exception as e:
                    await BotLog(level="error", message=f"Failed to send weekly reminder for guild {config.guild_id}: {e}").save()

    @weekly_activity_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(WeeklyActivity(bot))
