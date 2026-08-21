import subprocess
import sys
import threading
import os

def read_stream(stream, prefix, color_code):
    """Legge un flusso (stdout o stderr) e lo stampa con un prefisso colorato."""
    while True:
        line = stream.readline()
        if not line:
            break
        # Formattazione ANSI per i colori sul terminale
        colored_prefix = f"\033[{color_code}m{prefix}\033[0m"
        print(f"{colored_prefix} {line.strip()}", flush=True)

def main():
    print("🚀 Avvio del Discord Audio Broadcaster (DAB) Unificato...")
    
    # Path alle directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")
    bot_node_dir = os.path.join(base_dir, "bot-node")
    frontend_dir = os.path.join(base_dir, "frontend")
    guild_bot_dir = os.path.join(os.path.dirname(base_dir), "guild-bot")
    
    # Carica le variabili dal file .env nella root
    env_vars = os.environ.copy()
    root_env_path = os.path.join(base_dir, ".env")
    if os.path.exists(root_env_path):
        print("🔹 Caricamento variabili da .env...")
        with open(root_env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    val = val.strip()
                    # Rimuovi eventuali virgolette all'inizio e alla fine
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                    env_vars[key.strip()] = val
    else:
        print("⚠️ File .env non trovato nella root! Assicurati di rinominare .env.example in .env")

    # Determina l'eseguibile python dell'ambiente virtuale
    # Cerca prima nella root del dab-project, poi nella cartella padre
    venv_python = os.path.join(base_dir, ".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        parent_dir = os.path.dirname(base_dir)
        venv_python_parent = os.path.join(parent_dir, ".venv", "Scripts", "python.exe")
        if os.path.exists(venv_python_parent):
            venv_python = venv_python_parent
        else:
            venv_python = "python"
        
    print(f"🔹 Usando Python: {venv_python}")
    print("🔹 Avviando FastAPI (Web Dashboard)...")
    
    # Processo 1: FastAPI Web Server
    api_process = subprocess.Popen(
        [venv_python, "main_api.py"],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding='utf-8',
        errors='replace',
        env=env_vars
    )
    
    print("🔹 Avviando Node.js (Discord Bot Engine)...")
    # Processo 2: Node.js Bot
    npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"
    bot_process = subprocess.Popen(
        [npm_cmd, "start"],
        cwd=bot_node_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding='utf-8',
        errors='replace',
        env=env_vars
    )

    print("🔹 Avviando Vue 3 (Frontend)...")
    # Processo 3: Vue Frontend
    web_process = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding='utf-8',
        errors='replace',
        env=env_vars
    )
    print("🔹 Avviando Guild Bot (Python)...")
    # Processo 4: Guild Bot Python
    guild_bot_process = subprocess.Popen(
        [venv_python, "main.py"],
        cwd=guild_bot_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding='utf-8',
        errors='replace',
        env=env_vars
    )
    
    # Thread per leggere l'output senza bloccare
    # 32 = Verde (API), 36 = Ciano (BOT), 35 = Magenta (WEB), 33 = Giallo (GUILD BOT)
    threading.Thread(target=read_stream, args=(api_process.stdout, "[API]", "1;32"), daemon=True).start()
    threading.Thread(target=read_stream, args=(bot_process.stdout, "[BOT]", "1;36"), daemon=True).start()
    threading.Thread(target=read_stream, args=(web_process.stdout, "[WEB]", "1;35"), daemon=True).start()
    threading.Thread(target=read_stream, args=(guild_bot_process.stdout, "[GUILDBOT]", "1;33"), daemon=True).start()
    
    try:
        # Aspetta che uno dei processi termini
        api_process.wait()
        bot_process.wait()
        web_process.wait()
        guild_bot_process.wait()
    except KeyboardInterrupt:
        print("\n⏹️ Chiusura in corso...")
        api_process.terminate()
        bot_process.terminate()
        web_process.terminate()
        guild_bot_process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    # Abilita i colori ANSI su Windows Terminal
    if os.name == 'nt':
        os.system('color')
    main()
