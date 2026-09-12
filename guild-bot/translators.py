import os
import httpx
import urllib.parse

async def translate_mymemory(text: str, target_lang: str) -> str:
    langpair = f"Autodetect|{target_lang}"
    email = "admin@nyxpinguin.com"
    url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair={urllib.parse.quote(langpair)}&de={urllib.parse.quote(email)}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=15.0)
        response.raise_for_status()
        data = response.json()
        
        if data.get("responseStatus") == 200:
            return data["responseData"]["translatedText"]
        else:
            raise Exception(f"MyMemory Error: {data.get('responseDetails')}")

async def translate_deepl(text: str, target_lang: str) -> str:
    deepl_key = os.environ.get("DEEPL_AUTH_KEY")
    if not deepl_key:
        raise ValueError("Chiave API DeepL mancante (DEEPL_AUTH_KEY).")
    
    target = target_lang.upper()
    if target == "EN":
        target = "EN-US"
    elif target == "PT":
        target = "PT-BR"
        
    url = "https://api-free.deepl.com/v2/translate"
    headers = {
        "Authorization": f"DeepL-Auth-Key {deepl_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": [text],
        "target_lang": target
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=15.0)
        response.raise_for_status()
        data = response.json()
        return data["translations"][0]["text"]

async def translate_gemini(text: str, target_lang: str) -> str:
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        raise ValueError("Chiave API Gemini mancante (GEMINI_API_KEY).")
    
    # We use Google's official new SDK "google-genai" if possible, otherwise we use standard HTTP request.
    # Since we can't be sure if `google-genai` is installed in their venv, an HTTP request to Gemini REST API is safer and requires no dependencies.
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
    
    prompt = f"Translate the following text to {target_lang}. Reply ONLY with the translation, no extra text or quotes:\n\n{text}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=15.0)
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
