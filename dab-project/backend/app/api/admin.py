from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from app.models.models import AdminUser, GuildConfig, BotLog, ApiInstances
from app.api.oauth import get_current_admin

router = APIRouter()

def require_admin(admin: AdminUser = Depends(get_current_admin)):
    if admin.role != "admin":
        raise HTTPException(status_code=403, detail="Accesso riservato agli amministratori.")
    return admin

@router.get("/stats")
async def get_stats(admin: AdminUser = Depends(require_admin)):
    total_users = await AdminUser.count()
    total_configs = await GuildConfig.count()
    active_configs = await GuildConfig.find(GuildConfig.is_active == True).count()
    
    return {
        "total_users": total_users,
        "total_configs": total_configs,
        "active_configs": active_configs
    }

class UserCreateSchema(BaseModel):
    discord_id: str
    username: str
    role: str = "user"

class UserUpdateSchema(BaseModel):
    role: str

@router.get("/users")
async def get_users(admin: AdminUser = Depends(require_admin)):
    users = await AdminUser.find_all().to_list()
    return [{"discord_id": u.discord_id, "username": u.username, "role": u.role, "added_at": u.added_at.isoformat()} for u in users]

@router.post("/users")
async def add_user(data: UserCreateSchema, admin: AdminUser = Depends(require_admin)):
    existing = await AdminUser.find_one(AdminUser.discord_id == data.discord_id)
    if existing:
        raise HTTPException(status_code=400, detail="L'utente esiste già.")
    
    new_user = AdminUser(discord_id=data.discord_id, username=data.username, role=data.role)
    await new_user.save()
    return {"status": "success", "user": {"discord_id": new_user.discord_id, "username": new_user.username, "role": new_user.role}}

@router.put("/users/{discord_id}")
async def update_user(discord_id: str, data: UserUpdateSchema, admin: AdminUser = Depends(require_admin)):
    target_user = await AdminUser.find_one(AdminUser.discord_id == discord_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Utente non trovato.")
    
    target_user.role = data.role
    await target_user.save()
    return {"status": "success", "message": "Ruolo aggiornato."}

@router.delete("/users/{discord_id}")
async def delete_user(discord_id: str, admin: AdminUser = Depends(require_admin)):
    if discord_id == admin.discord_id:
        raise HTTPException(status_code=400, detail="Non puoi eliminare te stesso.")
    
    target_user = await AdminUser.find_one(AdminUser.discord_id == discord_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Utente non trovato.")
    
    await target_user.delete()
    return {"status": "success", "message": "Utente rimosso."}

class ApiInstancesSchema(BaseModel):
    piped: List[str]
    invidious: List[str]

@router.get("/instances")
async def get_instances(admin: AdminUser = Depends(require_admin)):
    config = await ApiInstances.find_one(ApiInstances.type == "config")
    if not config:
        return {"piped": [], "invidious": []}
    return {"piped": config.piped, "invidious": config.invidious}

@router.put("/instances")
async def update_instances(data: ApiInstancesSchema, admin: AdminUser = Depends(require_admin)):
    config = await ApiInstances.find_one(ApiInstances.type == "config")
    if not config:
        config = ApiInstances(type="config", piped=data.piped, invidious=data.invidious)
        await config.insert()
    else:
        config.piped = data.piped
        config.invidious = data.invidious
        await config.save()
    return {"status": "success"}

class GuildCreateSchema(BaseModel):
    name: str
    guild_id: str

@router.get("/guilds")
async def get_all_guilds(admin: AdminUser = Depends(require_admin)):
    guilds = await GuildConfig.find_all().to_list()
    return [{"guild_id": g.guild_id, "name": g.name, "member_role_id": g.member_role_id} for g in guilds]

@router.post("/guilds")
async def create_guild(data: GuildCreateSchema, admin: AdminUser = Depends(require_admin)):
    existing = await GuildConfig.find_one(GuildConfig.guild_id == data.guild_id)
    if existing:
        raise HTTPException(status_code=400, detail="Una Gilda con questo Discord ID esiste già.")
    
    new_guild = GuildConfig(guild_id=data.guild_id, name=data.name)
    await new_guild.save()
    return {"status": "success", "guild": {"guild_id": new_guild.guild_id, "name": new_guild.name}}

class GuildUpdateSchema(BaseModel):
    name: str

@router.put("/guilds/{guild_id}")
async def update_guild(guild_id: str, data: GuildUpdateSchema, admin: AdminUser = Depends(require_admin)):
    target_guild = await GuildConfig.find_one(GuildConfig.guild_id == guild_id)
    if not target_guild:
        raise HTTPException(status_code=404, detail="Gilda non trovata.")
    
    target_guild.name = data.name
    await target_guild.save()
    return {"status": "success", "guild": {"guild_id": target_guild.guild_id, "name": target_guild.name}}

@router.delete("/guilds/{guild_id}")
async def delete_guild(guild_id: str, admin: AdminUser = Depends(require_admin)):
    target_guild = await GuildConfig.find_one(GuildConfig.guild_id == guild_id)
    if not target_guild:
        raise HTTPException(status_code=404, detail="Gilda non trovata.")
    
    await target_guild.delete()
    return {"status": "success", "message": "Gilda rimossa."}
