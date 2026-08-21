from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
import httpx
import os
from app.core.config import settings

router = APIRouter()

DISCORD_API_BASE = "https://discord.com/api/v10"

@router.get("/login")
async def login(state: str = None):
    url = (
        f"https://discord.com/oauth2/authorize?client_id={settings.DISCORD_CLIENT_ID}"
        f"&redirect_uri={settings.DISCORD_REDIRECT_URI}&response_type=code&scope=identify%20guilds"
    )
    if state:
        url += f"&state={state}"
    return RedirectResponse(url)

import jwt
from datetime import datetime, timedelta
from app.models.models import AdminUser

@router.get("/callback")
async def callback(code: str, state: str = None):
    data = {
        "client_id": settings.DISCORD_CLIENT_ID,
        "client_secret": settings.DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.DISCORD_REDIRECT_URI,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{DISCORD_API_BASE}/oauth2/token", data=data, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid code")
        
        token_data = response.json()
        access_token = token_data["access_token"]

        # Fetch user profile from Discord
        user_response = await client.get(
            f"{DISCORD_API_BASE}/users/@me", 
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch user profile")
            
        user_info = user_response.json()
        discord_id = user_info["id"]

        # Fetch user guilds from Discord
        guilds_response = await client.get(
            f"{DISCORD_API_BASE}/users/@me/guilds",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_guilds = []
        user_guilds_info = []
        if guilds_response.status_code == 200:
            guilds_data = guilds_response.json()
            user_guilds = [g["id"] for g in guilds_data]
            user_guilds_info = [{"id": g["id"], "name": g["name"], "icon": g.get("icon")} for g in guilds_data]

        from app.models.models import GuildConfig
        app_guilds = await GuildConfig.find().to_list()
        app_guild_ids = [g.guild_id for g in app_guilds]

        # Check if user is an admin for global DAB app
        admin = await AdminUser.find_one(AdminUser.discord_id == discord_id)
        global_role = admin.role if admin else "user"

        valid_guild_ids = [g_id for g_id in user_guilds if g_id in app_guild_ids]
        valid_guilds_info = [g_info for g_info in user_guilds_info if g_info["id"] in app_guild_ids]

        frontend_url = os.getenv("FRONTEND_URL", "")

        if not admin and len(valid_guild_ids) == 0:
            return RedirectResponse(f"{frontend_url}/login?error=unauthorized")

        from app.models.guild_drops import DropUser
        drop_user = await DropUser.find_one(DropUser.discord_id == discord_id)
        if not drop_user:
            drop_user = DropUser(discord_id=discord_id, username=user_info.get("username"), avatar=user_info.get("avatar"), guilds=valid_guild_ids, guilds_info=valid_guilds_info)
        else:
            drop_user.username = user_info.get("username")
            drop_user.avatar = user_info.get("avatar")
            drop_user.guilds = valid_guild_ids
            drop_user.guilds_info = valid_guilds_info
        await drop_user.save()

        # Generate jwt
        expiration = datetime.utcnow() + timedelta(hours=24)
        jwt_payload = {
            "sub": discord_id,
            "username": user_info.get("username"),
            "role": global_role,
            "exp": expiration
        }
        session_token = jwt.encode(jwt_payload, settings.DISCORD_CLIENT_SECRET, algorithm="HS256")

        redirect_url = f"{frontend_url}/login?token={session_token}"
        if state:
            redirect_url += f"&guild={state}"
            
        return RedirectResponse(redirect_url)


from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/oauth/login")

async def get_current_admin(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.DISCORD_CLIENT_SECRET, algorithms=["HS256"])
        discord_id = payload.get("sub")
        if discord_id is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        admin = await AdminUser.find_one(AdminUser.discord_id == discord_id)
        if admin is None or admin.role != "admin":
            raise HTTPException(status_code=403, detail="Non più autorizzato")
        return admin
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_guild_admin(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.DISCORD_CLIENT_SECRET, algorithms=["HS256"])
        discord_id = payload.get("sub")
        if discord_id is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        admin = await AdminUser.find_one(AdminUser.discord_id == discord_id)
        if admin is None or admin.role not in ["admin", "guild_admin"]:
            raise HTTPException(status_code=403, detail="Non autorizzato (richiesto ruolo admin o guild_admin)")
        return admin
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

from app.models.guild_drops import DropUser
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.DISCORD_CLIENT_SECRET, algorithms=["HS256"])
        discord_id = payload.get("sub")
        if discord_id is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user = await DropUser.find_one(DropUser.discord_id == discord_id)
        if user is None:
            raise HTTPException(status_code=403, detail="Utente non trovato")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
