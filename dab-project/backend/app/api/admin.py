from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from app.models.models import AdminUser, GuildConfig, BotLog
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
