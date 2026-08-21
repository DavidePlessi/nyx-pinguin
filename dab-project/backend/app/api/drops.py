from fastapi import APIRouter, HTTPException, Depends
from app.api.oauth import get_current_user, get_current_admin, get_current_guild_admin
from app.models.guild_drops import DropUser, Build, BuildSlots, DropHistory, DropPoll
from app.models.models import GuildConfig
from typing import List, Optional
from datetime import datetime
import httpx
from bson import ObjectId
from app.core.config import settings

router = APIRouter()

# --- Users ---

@router.get("/me")
async def get_me(user: DropUser = Depends(get_current_user)):
    return user

# --- Guild Config ---

@router.get("/guilds/{guild_id}/config")
async def get_guild_drops_config(guild_id: str, admin = Depends(get_current_admin)):
    config = await GuildConfig.find_one(GuildConfig.guild_id == guild_id)
    if not config:
        raise HTTPException(status_code=404, detail="Guild config non trovata")
    return {"member_role_id": config.member_role_id}

@router.post("/guilds/{guild_id}/config")
async def set_guild_drops_config(guild_id: str, member_role_id: str, admin = Depends(get_current_admin)):
    config = await GuildConfig.find_one(GuildConfig.guild_id == guild_id)
    if not config:
        config = GuildConfig(guild_id=guild_id)
    config.member_role_id = member_role_id
    await config.save()
    return {"status": "success", "member_role_id": config.member_role_id}

# --- Builds ---

@router.get("/guilds/{guild_id}/builds")
async def get_my_build(guild_id: str, user: DropUser = Depends(get_current_user)):
    build = await Build.find_one(Build.user_id == user.discord_id, Build.guild_id == guild_id)
    return build # Potrebbe essere null se non l'ha ancora creata

@router.post("/guilds/{guild_id}/builds")
async def save_my_build(guild_id: str, payload: dict, user: DropUser = Depends(get_current_user)):
    from app.models.guild_drops import WeaponClassMapping
    # Validate payload
    try:
        slots_data = payload.get("slots", {})
        build_slots = BuildSlots(**slots_data)
        character_name = payload.get("character_name")
        play_style = payload.get("play_style")
        questlog_url = payload.get("questlog_url")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Dati build non validi: {str(e)}")
        
    # Calcolo della classe
    computed_class = None
    if build_slots.main_weapon and build_slots.secondary_weapon:
        w1 = build_slots.main_weapon.subCategory.lower()
        w2 = build_slots.secondary_weapon.subCategory.lower()
        # Cerchiamo la classe (l'ordine non importa)
        mapping = await WeaponClassMapping.find_one(
            {
                "$or": [
                    {"weapon_1": w1, "weapon_2": w2},
                    {"weapon_1": w2, "weapon_2": w1}
                ]
            }
        )
        if mapping:
            computed_class = mapping.class_name

    build = await Build.find_one(Build.user_id == user.discord_id, Build.guild_id == guild_id)
    if not build:
        build = Build(
            user_id=user.discord_id, 
            guild_id=guild_id, 
            slots=build_slots,
            character_name=character_name,
            character_class=computed_class,
            play_style=play_style,
            questlog_url=questlog_url
        )
    else:
        build.slots = build_slots
        if character_name is not None: build.character_name = character_name
        build.character_class = computed_class
        if play_style is not None: build.play_style = play_style
        if questlog_url is not None: build.questlog_url = questlog_url
        build.updated_at = datetime.utcnow()
    
    # Se modifico una build primary o pending, torna draft?
    # Il piano dice: "L'utente invia la build per renderla Primaria". Quindi il salvataggio è una cosa, l'invio in pending un'altra.
    # Quando l'utente salva modifiche, torna in draft per evitare truffe post-approvazione.
    build.status = "draft"
    
    await build.save()
    return build

@router.post("/guilds/{guild_id}/builds/submit")
async def submit_my_build(guild_id: str, user: DropUser = Depends(get_current_user)):
    build = await Build.find_one(Build.user_id == user.discord_id, Build.guild_id == guild_id)
    if not build:
        raise HTTPException(status_code=404, detail="Nessuna build trovata")
    
    build.status = "pending"
    build.updated_at = datetime.utcnow()
    await build.save()
    return build

# Admin: View all pending builds
@router.get("/admin/guilds/{guild_id}/builds/pending")
async def get_pending_builds(guild_id: str, admin = Depends(get_current_guild_admin)):
    builds = await Build.find(Build.guild_id == guild_id, Build.status == "pending").to_list()
    # Arricchiamo con info utente
    result = []
    for b in builds:
        u = await DropUser.find_one(DropUser.discord_id == b.user_id)
        result.append({
            "build": b,
            "user": u
        })
    return result

# Admin: View ALL builds
@router.get("/admin/guilds/{guild_id}/builds")
async def get_all_builds(guild_id: str, admin = Depends(get_current_guild_admin)):
    builds = await Build.find(Build.guild_id == guild_id).to_list()
    # Arricchiamo con info utente
    result = []
    for b in builds:
        u = await DropUser.find_one(DropUser.discord_id == b.user_id)
        result.append({
            "build": b,
            "user": u
        })
    return result

# Admin: Approve build
@router.post("/admin/guilds/{guild_id}/builds/{build_id}/approve")
async def approve_build(guild_id: str, build_id: str, admin = Depends(get_current_guild_admin)):
    from bson import ObjectId
    build = await Build.get(ObjectId(build_id))
    if not build or build.guild_id != guild_id:
        raise HTTPException(status_code=404, detail="Build non trovata")
    
    # Demota le altre build primary dello stesso utente (teoricamente ce n'è solo una, ma per sicurezza)
    old_primary = await Build.find_one(Build.user_id == build.user_id, Build.guild_id == guild_id, Build.status == "primary")
    if old_primary and old_primary.id != build.id:
        old_primary.status = "draft"
        await old_primary.save()

    build.status = "primary"
    build.updated_at = datetime.utcnow()
    await build.save()
    return build

# --- Drop History ---
@router.get("/guilds/{guild_id}/history")
async def get_drop_history(guild_id: str, user: DropUser = Depends(get_current_user)):
    history = await DropHistory.find(DropHistory.guild_id == guild_id).sort(-DropHistory.assigned_at).to_list(length=100)
    
    # Raccogli ID utenti unici
    user_ids = list(set([h.user_id for h in history]))
    users = await DropUser.find({"discord_id": {"$in": user_ids}}).to_list()
    user_map = {u.discord_id: {"username": u.username, "avatar": u.avatar} for u in users}
    
    result = []
    for h in history:
        h_dict = h.model_dump()
        u_info = user_map.get(h.user_id, {"username": h.user_id, "avatar": None})
        h_dict["user"] = u_info
        result.append(h_dict)
        
    return result

# Public API for frontend to fetch class mappings
@router.get("/classes")
async def get_weapon_classes():
    from app.models.guild_drops import WeaponClassMapping
    classes = await WeaponClassMapping.find_all().to_list()
    return classes

@router.post("/admin/guilds/{guild_id}/history")
async def add_drop_history_manual(guild_id: str, item_id: str, item_name: str, user_id: str, category: str, admin = Depends(get_current_guild_admin)):
    entry = DropHistory(
        guild_id=guild_id,
        item_id=item_id,
        item_name=item_name,
        user_id=user_id,
        category=category,
        assigned_by=admin.discord_id
    )
    await entry.save()
    return entry

# --- Polls ---

@router.get("/guilds/{guild_id}/polls")
async def get_polls(guild_id: str, admin = Depends(get_current_guild_admin)):
    polls = await DropPoll.find(DropPoll.guild_id == guild_id, DropPoll.status == "open").sort("-created_at").to_list()
    results = []
    for p in polls:
        c_info = []
        for c_id in p.candidates:
            user = await DropUser.find_one(DropUser.discord_id == c_id)
            c_info.append({
                "discord_id": c_id,
                "username": user.username if user else "Unknown"
            })
        p_dict = p.model_dump()
        p_dict["candidates_info"] = c_info
        p_dict["id"] = str(p.id)
        results.append(p_dict)
    return results

from pydantic import BaseModel
class AddCandidatePayload(BaseModel):
    user_id: str

@router.post("/guilds/{guild_id}/polls/{poll_id}/candidates")
async def add_candidate(guild_id: str, poll_id: str, payload: AddCandidatePayload, admin = Depends(get_current_guild_admin)):
    poll = await DropPoll.get(ObjectId(poll_id))
    if not poll or poll.guild_id != guild_id:
        raise HTTPException(404, "Poll not found")
    if payload.user_id not in poll.candidates:
        poll.candidates.append(payload.user_id)
        await poll.save()
    return {"status": "success"}

@router.delete("/guilds/{guild_id}/polls/{poll_id}/candidates/{user_id}")
async def remove_candidate(guild_id: str, poll_id: str, user_id: str, admin = Depends(get_current_guild_admin)):
    poll = await DropPoll.get(ObjectId(poll_id))
    if not poll or poll.guild_id != guild_id:
        raise HTTPException(404, "Poll not found")
    if user_id in poll.candidates:
        poll.candidates.remove(user_id)
        await poll.save()
    return {"status": "success"}

class AssignPayload(BaseModel):
    user_id: str
    category: str

@router.post("/guilds/{guild_id}/polls/{poll_id}/assign")
async def assign_poll(guild_id: str, poll_id: str, payload: AssignPayload, admin: DropUser = Depends(get_current_guild_admin)):
    poll = await DropPoll.get(ObjectId(poll_id))
    if not poll or poll.guild_id != guild_id:
        raise HTTPException(404, "Poll not found")
    if poll.status != "open":
        raise HTTPException(400, "Poll already closed")
    
    poll.status = "closed"
    await poll.save()
    
    # Crea history
    history = DropHistory(
        guild_id=guild_id,
        user_id=payload.user_id,
        item_id=poll.item_id,
        item_name=poll.item_name,
        category=payload.category,
        assigned_by=admin.discord_id
    )
    await history.save()
    
    if poll.channel_id and settings.GUILD_BOT_TOKEN:
        winner_mention = f"<@{payload.user_id}>"
        all_participants = [f"<@{c}>" for c in poll.candidates]
        
        embed = {
            "title": f"🎉 Drop Assegnato!",
            "description": f"L'oggetto **{poll.item_name}** è stato assegnato a {winner_mention}.",
            "color": 3066993,
            "fields": []
        }
        if all_participants:
            embed["fields"].append({
                "name": "Partecipanti al Drop",
                "value": " ".join(all_participants)
            })
            
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bot {settings.GUILD_BOT_TOKEN}",
                "Content-Type": "application/json"
            }
            try:
                # 1. Rimuovi il bottone dal messaggio originale del sondaggio
                if poll.message_id:
                    await client.patch(
                        f"https://discord.com/api/v10/channels/{poll.channel_id}/messages/{poll.message_id}",
                        json={"components": []},
                        headers=headers
                    )
                
                # 2. Invia il messaggio di assegnazione
                res = await client.post(
                    f"https://discord.com/api/v10/channels/{poll.channel_id}/messages",
                    json={"embeds": [embed]},
                    headers=headers
                )
            except Exception as e:
                print("Error sending discord msg:", e)
            
@router.post("/guilds/{guild_id}/polls/{poll_id}/cancel")
async def cancel_poll(guild_id: str, poll_id: str, admin = Depends(get_current_guild_admin)):
    poll = await DropPoll.get(ObjectId(poll_id))
    if not poll or poll.guild_id != guild_id:
        raise HTTPException(404, "Poll not found")
    if poll.status != "open":
        raise HTTPException(400, "Poll already closed")
    
    poll.status = "canceled"
    await poll.save()
    
    if poll.channel_id and settings.GUILD_BOT_TOKEN:
        embed = {
            "title": "🛑 Drop Annullato",
            "description": f"Il sondaggio per **{poll.item_name}** è stato annullato dagli admin senza assegnazioni.",
            "color": 15158332
        }
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bot {settings.GUILD_BOT_TOKEN}",
                "Content-Type": "application/json"
            }
            try:
                # 1. Rimuovi i bottoni dal sondaggio
                if poll.message_id:
                    await client.patch(
                        f"https://discord.com/api/v10/channels/{poll.channel_id}/messages/{poll.message_id}",
                        json={"components": []},
                        headers=headers
                    )
                # 2. Invia notifica di annullamento
                await client.post(
                    f"https://discord.com/api/v10/channels/{poll.channel_id}/messages",
                    json={"embeds": [embed]},
                    headers=headers
                )
            except Exception as e:
                pass
            
    return {"status": "success"}
