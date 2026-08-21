from fastapi import APIRouter, HTTPException, Query
import httpx

router = APIRouter()

QUESTLOG_API_URL = "https://questlog.gg/throne-and-liberty/api/trpc/database.getItems"

# Semplice cache in memory (opzionale, per evitare di colpire le API per ogni keystroke dell'autocomplete se serve)
_cache = {}

@router.get("/items")
async def get_items(input: str = Query(..., description="Query JSON codificata per l'API di questlog")):
    if input in _cache:
        return _cache[input]

    async with httpx.AsyncClient() as client:
        try:
            # Passa la query param "input" esattamente come ricevuta
            res = await client.get(QUESTLOG_API_URL, params={"input": input})
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail="Errore dal server Questlog")
            
            data = res.json()
            # Salviamo in cache per evitare troppe chiamate (potrebbe essere limitato)
            # Idealmente con TTL o limitata, per ora semplice dict
            if len(_cache) > 1000:
                _cache.clear()
            _cache[input] = data
            return data
        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail=f"Errore di connessione a Questlog: {str(exc)}")

from fastapi.responses import Response

@router.get("/image")
async def proxy_image(path: str = Query(..., description="Path immagine es. /tl/item/icon")):
    if not path.startswith("/"):
        path = "/" + path
        
    # Gli asset spesso arrivano come /.../NomeFile.NomeFile, noi vogliamo solo la prima parte
    clean_path = path.split('.')[0]
    
    # Example item.icon: /assets/Game/Image/Icon/Item_128/Equip/Weapon/IT_P_Wand_00011A
    url = f"https://cdn.questlog.gg/throne-and-liberty{clean_path}.webp"
    
    print(f"[DEBUG PROXY IMAGE] Richiesta immagine per path originale: {path}")
    print(f"[DEBUG PROXY IMAGE] Costruito URL CDN: {url}")
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url)
            print(f"[DEBUG PROXY IMAGE] Risposta da CDN: {res.status_code}")
            if res.status_code != 200:
                print(f"[DEBUG PROXY IMAGE] Errore body: {res.text[:200]}")
                raise HTTPException(status_code=res.status_code, detail="Immagine non trovata")
            
            return Response(content=res.content, media_type="image/webp")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail="Errore proxy immagine")

import urllib.parse
import json
import asyncio

@router.get("/import-build")
async def import_build(url: str = Query(..., description="L'URL o lo slug della build di Questlog")):
    # 1. Estrai lo slug se viene fornito l'URL
    slug = url.split('/')[-1] if '/' in url else url
    
    questlog_build_api = f'https://questlog.gg/throne-and-liberty/api/trpc/characterBuilder.getCharacter?input={{"slug":"{slug}"}}'
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(questlog_build_api)
            if res.status_code != 200:
                raise HTTPException(status_code=400, detail="Impossibile recuperare la build da Questlog")
            
            data = res.json()
            if not data.get("result") or not data["result"].get("data") or not data["result"]["data"].get("builds"):
                raise HTTPException(status_code=404, detail="Nessuna build valida trovata a questo link")
                
            build_data = data["result"]["data"]["builds"][0]
            equipment = build_data.get("equipment", {})
            
            # Mapping degli slot: Questlog -> nostro DB
            slot_mapping = {
                "main_hand": "main_weapon",
                "off_hand": "secondary_weapon",
                "belt": "belt",
                "necklace": "necklace",
                "bracelet": "bracelet",
                "ring_1": "ring_1",
                "ring_2": "ring_2",
                "brooch": "brooch",
                "cloak": "cloak",
                "legs": "legs",
                "hands": "hands",
                "feet": "feet",
                "head": "head",
                "chest": "chest"
            }
            
            mapped_slots = {}
            tasks = []
            
            # Helper function for fetching item details
            async def fetch_item(ql_slot, our_slot, item_id):
                item_url = f'https://questlog.gg/throne-and-liberty/api/trpc/database.getItem?input={{"id":"{item_id}","language":"en"}}'
                try:
                    item_res = await client.get(item_url)
                    if item_res.status_code == 200:
                        item_data = item_res.json()
                        if item_data.get("result") and item_data["result"].get("data"):
                            details = item_data["result"]["data"]
                            # Build the format expected by BuildSlotItem
                            return our_slot, {
                                "id": details.get("id"),
                                "name": details.get("name"),
                                "icon": details.get("icon"),
                                "mainCategory": details.get("mainCategory"),
                                "subCategory": details.get("subCategory")
                            }
                except Exception:
                    pass
                return our_slot, None

            for ql_slot, item_data in equipment.items():
                if ql_slot in slot_mapping and item_data and "id" in item_data and item_data["id"]:
                    tasks.append(fetch_item(ql_slot, slot_mapping[ql_slot], item_data["id"]))
            
            results = await asyncio.gather(*tasks)
            for our_slot, item_info in results:
                if item_info:
                    mapped_slots[our_slot] = item_info
            
            return {"status": "success", "slots": mapped_slots}
            
        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail=f"Errore di rete durante l'importazione: {str(exc)}")
