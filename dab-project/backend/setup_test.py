import asyncio
import os
import sys

# Aggiungi il path per l'import corretto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from app.models.models import GuildConfig

async def main():
    print("Connessione a MongoDB...")
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB_NAME]
    await init_beanie(database=db, document_models=[GuildConfig])
    
    print("\n=== Configurazione Test per il Bot ===")
    print("Per trovare gli ID su Discord: Vai su Impostazioni Utente -> Avanzate -> Attiva Modalità Sviluppatore.")
    print("Poi fai tasto destro sul nome del server o del canale e clicca 'Copia ID'.\n")
    
    guild_id = input("1. Inserisci l'ID del Server (Guild ID): ").strip()
    source_id = input("2. Inserisci l'ID del Canale Vocale Sorgente: ").strip()
    dest_ids_raw = input("3. Inserisci gli ID dei Canali Vocali di Destinazione (separati da virgola): ").strip()
    
    dest_ids = [d.strip() for d in dest_ids_raw.split(",") if d.strip()]
    
    # Rimuovi vecchie configurazioni per questo server se esistono
    vecchie_config = await GuildConfig.find(GuildConfig.guild_id == guild_id).to_list()
    if vecchie_config:
        for c in vecchie_config:
            await c.delete()
    
    # Crea la nuova configurazione
    config = GuildConfig(
        guild_id=guild_id,
        source_channel_id=source_id,
        dest_channels=dest_ids,
        is_active=True
    )
    await config.insert()
    print("\n✅ Configurazione salvata con successo in MongoDB!")
    print("Ora puoi andare sul tuo server Discord e digitare /pinguin_on_duty")

if __name__ == "__main__":
    asyncio.run(main())
