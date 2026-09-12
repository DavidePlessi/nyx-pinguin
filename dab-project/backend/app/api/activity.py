from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from app.models.models import GuildConfig, WeeklyGameActivity
from app.models.activity import PlayerActivity, EventTrack
from app.services.raid_helper import fetch_and_store_raid_helper_activity
import logging
from datetime import datetime, timedelta, timezone

router = APIRouter()
logger = logging.getLogger(__name__)

from app.api.oauth import get_current_user

@router.get("/{guild_id}")
async def get_activity(
    guild_id: str, 
    from_date: Optional[str] = None, 
    to_date: Optional[str] = None, 
    target_week_id: Optional[str] = None,
    user = Depends(get_current_user)
) -> Dict[str, Any]:
    query = {"guild_id": guild_id}
    
    if from_date or to_date:
        query["date"] = {}
        if from_date:
            try:
                fd = datetime.fromisoformat(from_date)
                query["date"]["$gte"] = fd
            except ValueError:
                pass
        if to_date:
            try:
                td = datetime.fromisoformat(to_date)
                query["date"]["$lte"] = td
            except ValueError:
                pass
        if not query["date"]:
            del query["date"]

    activities = await PlayerActivity.find(query).to_list()
    
    # Per total_events_in_period count unique event_ids from EventTrack in the same date range
    # Wait, EventTrack has processed_at, but we need the event's date. 
    # Since PlayerActivity holds the event date, we can just find distinct event_id in activities!
    unique_events = set(act.event_id for act in activities)
    total_events_in_period = len(unique_events)
    
    player_data = {}
    weekly_data = {}
    event_data = {}
    
    for act in activities:
        pid = act.player_id
        eid = act.event_id
        
        if pid not in player_data:
            player_data[pid] = {
                "player_id": pid,
                "player_name": act.player_name,
                "total_events": 0,
                "events": [],
                "weekly_game_activity": 0,
                "has_current_weekly_activity": False
            }
        player_data[pid]["total_events"] += 1
        player_data[pid]["events"].append({
            "event_id": eid,
            "event_name": act.event_name,
            "date": act.date.isoformat(),
            "source": act.source
        })
        
        if eid not in event_data:
            event_data[eid] = {
                "event_id": eid,
                "event_name": act.event_name,
                "date": act.date.isoformat(),
                "source": act.source,
                "participants": []
            }
        event_data[eid]["participants"].append({
            "player_id": act.player_id,
            "player_name": act.player_name
        })
        
        year, week, _ = act.date.isocalendar()
        week_str = f"{year}-W{week:02d}"
        if week_str not in weekly_data:
            weekly_data[week_str] = {}
        if pid not in weekly_data[week_str]:
            weekly_data[week_str][pid] = 0
        weekly_data[week_str][pid] += 1
        
    now = datetime.utcnow()
    
    if target_week_id:
        current_week_str = target_week_id
        try:
            year_part, week_part = target_week_id.split('-W')
            y = int(year_part)
            w = int(week_part)
            # Monday of the target ISO week
            target_date = datetime.strptime(f"{y}-W{w}-1", "%Y-W%W-%w")
        except:
            target_date = now
    else:
        year, week, _ = now.isocalendar()
        current_week_str = f"{year}-W{week:02d}"
        target_date = now
    
    all_weekly_scores_db = await WeeklyGameActivity.find(
        WeeklyGameActivity.guild_id == guild_id
    ).to_list()
    
    weekly_scores_map = {}
    weekly_scores_history = {}
    
    for wa in all_weekly_scores_db:
        if wa.week_id == current_week_str:
            weekly_scores_map[wa.player_id] = wa.activity_score
            
        if wa.player_id not in weekly_scores_history:
            weekly_scores_history[wa.player_id] = []
        weekly_scores_history[wa.player_id].append({
            "week_id": wa.week_id,
            "score": wa.activity_score,
            "reported_at": wa.reported_at.isoformat()
        })
    
    guild = await GuildConfig.find_one(GuildConfig.guild_id == guild_id)
    target_day = guild.weekly_activity_day if guild else 3
    drop_min_events = guild.drop_min_events if guild else 2
    drop_min_weekly_activity = guild.drop_min_weekly_activity if guild else 5500
    
    days_until_target = (target_day - target_date.weekday()) % 7
    week_end = target_date + timedelta(days=days_until_target)
    week_end = week_end.replace(hour=23, minute=59, second=59, microsecond=999999)
    week_start = week_end - timedelta(days=6)
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    recent_activities = await PlayerActivity.find(
        PlayerActivity.guild_id == guild_id,
        PlayerActivity.date >= week_start,
        PlayerActivity.date <= week_end
    ).to_list()
    
    recent_events_count = {}
    for act in recent_activities:
        if act.player_id not in recent_events_count:
            recent_events_count[act.player_id] = set()
        recent_events_count[act.player_id].add(act.event_id)
        
    # Ensure players that only have WeeklyGameActivity (no Raid Helper events) are included
    for wa in all_weekly_scores_db:
        if wa.player_id not in player_data:
            player_data[wa.player_id] = {
                "player_id": wa.player_id,
                "player_name": wa.player_name,
                "total_events": 0,
                "events": [],
                "weekly_game_activity": 0,
                "has_current_weekly_activity": False
            }
    
    for p in player_data.values():
        p["weekly_game_activity"] = weekly_scores_map.get(p["player_id"], 0)
        p["has_current_weekly_activity"] = p["player_id"] in weekly_scores_map
        p["weekly_activity_history"] = sorted(weekly_scores_history.get(p["player_id"], []), key=lambda x: x["week_id"], reverse=True)
        
        pvp_events_count = len(recent_events_count.get(p["player_id"], set()))
        p["recent_pvp_events"] = pvp_events_count
        p["is_eligible_for_drop"] = (
            pvp_events_count >= drop_min_events 
            or p["weekly_game_activity"] > drop_min_weekly_activity
        )
        
    return {
        "total_events": total_events_in_period,
        "players": list(player_data.values()),
        "events": list(event_data.values()),
        "weekly_data": weekly_data,
        "target_week_start": week_start.isoformat(),
        "target_week_end": week_end.isoformat(),
        "drop_config": {
            "min_events": drop_min_events,
            "min_weekly_activity": drop_min_weekly_activity,
            "weekly_activity_day": target_day
        }
    }

from app.api.oauth import get_current_guild_admin

@router.post("/sync/{guild_id}")
async def sync_activity(guild_id: str, admin = Depends(get_current_guild_admin)):
    guild = await GuildConfig.find_one(GuildConfig.guild_id == guild_id)
    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found")
        
    if not guild.raid_helper_api_key:
        raise HTTPException(status_code=400, detail="Raid-Helper API key not configured for this guild")
        
    await fetch_and_store_raid_helper_activity(guild)
    return {"status": "success", "message": "Activity synchronized successfully"}

import httpx
from app.core.config import settings
from app.models.models import BotLog

@router.post("/trigger_log_message/{guild_id}")
async def trigger_log_message(guild_id: str, week_id: Optional[str] = None, admin = Depends(get_current_guild_admin)):
    config = await GuildConfig.find_one(GuildConfig.guild_id == guild_id)
    if not config or not getattr(config, "weekly_activity_enabled", False):
        raise HTTPException(status_code=400, detail="Weekly activity tracking is not enabled for this server.")
    
    channel_id = getattr(config, "weekly_activity_channel_id", None)
    if not channel_id:
        raise HTTPException(status_code=400, detail="Weekly activity channel ID not configured.")
        
    target_day = getattr(config, "weekly_activity_day", 3)
    
    if not week_id:
        now = datetime.utcnow()
        days_until_target = (target_day - now.weekday()) % 7
        target_date = now + timedelta(days=days_until_target)
        year, week, _ = target_date.isocalendar()
        week_id = f"{year}-W{week:02d}"
    else:
        # compute target date from week_id string
        y_str, w_str = week_id.split("-W")
        y, w = int(y_str), int(w_str)
        # Monday of the ISO week
        iso_mon = datetime.strptime(f'{y} {w} 1', '%G %V %u')
        target_date = iso_mon + timedelta(days=target_day)

    week_start = target_date - timedelta(days=6)
    date_range_str = f"{week_start.strftime('%d/%m/%Y')} - {target_date.strftime('%d/%m/%Y')}"
    
    lang = getattr(config, "bot_language", "en")
    
    locales = {
        "en": {
            "title": "📊 Weekly Activity Log",
            "desc": "{role_mention} It's time to log your weekly in-game activity!\n\nPlease click the button below to submit your score for **{week_id}** ({date_range}).",
            "btn": "Log Activity"
        },
        "it": {
            "title": "📊 Log Attività Settimanale",
            "desc": "{role_mention} È il momento di registrare la tua attività settimanale!\n\nClicca il pulsante qui sotto per inviare il tuo punteggio per **{week_id}** ({date_range}).",
            "btn": "Registra Attività"
        },
        "fr": {
            "title": "📊 Journal d'Activité Hebdomadaire",
            "desc": "{role_mention} Il est temps d'enregistrer votre activité hebdomadaire!\n\nVeuillez cliquer sur le bouton ci-dessous pour soumettre votre score pour **{week_id}** ({date_range}).",
            "btn": "Enregistrer l'activité"
        },
        "es": {
            "title": "📊 Registro de Actividad Semanal",
            "desc": "{role_mention} ¡Es hora de registrar tu actividad semanal!\n\nHaz clic en el botón de abajo para enviar tu puntuación de **{week_id}** ({date_range}).",
            "btn": "Registrar Actividad"
        },
        "de": {
            "title": "📊 Wöchentliches Aktivitätsprotokoll",
            "desc": "{role_mention} Es ist Zeit, deine wöchentliche Aktivität einzutragen!\n\nBitte klicke auf den Button unten, um deine Punktzahl für **{week_id}** ({date_range}) zu übermitteln.",
            "btn": "Aktivität eintragen"
        }
    }
    
    t = locales.get(lang, locales["en"])
    
    role_mention = f"<@&{config.member_role_id}>" if getattr(config, "member_role_id", None) else ""
    description = t["desc"].replace("{role_mention}", role_mention).replace("{week_id}", week_id).replace("{date_range}", date_range_str)
    
    payload = {
        "content": "",
        "embeds": [
            {
                "title": t["title"],
                "description": description,
                "color": 3447003
            }
        ],
        "components": [
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "style": 1,
                        "label": t["btn"],
                        "custom_id": f"log_activity_btn:{week_id}",
                        "emoji": {
                            "name": "📝"
                        }
                    }
                ]
            }
        ]
    }
    
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"https://discord.com/api/v10/channels/{channel_id}/messages",
            headers={"Authorization": f"Bot {settings.GUILD_BOT_TOKEN}", "Content-Type": "application/json"},
            json=payload
        )
        if res.status_code not in (200, 201):
            raise HTTPException(status_code=500, detail=f"Discord API Error: {res.text}")
            
    await BotLog(level="info", message=f"Manual trigger: Sent weekly activity announcement for guild {guild_id} (Week {week_id}).").save()
    return {"status": "success", "message": "Announcement message sent to Discord."}
