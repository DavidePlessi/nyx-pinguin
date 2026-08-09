import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.router import api_router
from app.core.db import init_db, close_db
from app.core.ipc import init_ipc

app = FastAPI(title="Discord Audio Broadcaster API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production it's served on same host anyway
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    await init_db()
    await init_ipc()

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()

# Montaggio file statici Vue
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_vue_app(full_path: str):
        # Escludi le rotte API (gestite sopra)
        if full_path.startswith("api/"):
            return {"error": "Not Found"}
            
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        # Catch-all: ritorna index.html per la SPA
        return FileResponse(os.path.join(frontend_dist, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_api:app", host="0.0.0.0", port=8000, reload=True)
