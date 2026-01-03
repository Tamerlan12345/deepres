from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import logging
import sys
from app.config import settings
from app.database import init_db, AsyncSessionLocal
from app.api import router as api_router
from app.models import User
from contextlib import asynccontextmanager
from passlib.context import CryptContext
from sqlalchemy import select

# --- FIX LOGGING START ---
# Настройка логгера, чтобы он писал в консоль (stdout), которую видит Docker
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("app")
# --- FIX LOGGING END ---

# Password Context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin_user():
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(select(User).where(User.username == "admin"))
            user = result.scalars().first()
            if not user:
                hashed_pw = pwd_context.hash("123456")
                new_user = User(username="admin", hashed_password=hashed_pw)
                session.add(new_user)
                await session.commit()
                logger.info("Admin user created: admin / 123456")
            else:
                logger.info("Admin user already exists")
        except Exception as e:
            logger.error(f"Error creating admin user: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 ЗАПУСК БЭКЕНДА CENTRAS AI AGENT...")
    await init_db()
    # Сюда добавить создание админа, если еще не добавили
    await create_admin_user()
    logger.info("✅ База данных инициализирована.")
    yield
    logger.info("🛑 Остановка бэкенда.")

app = FastAPI(title="Centras Strategic AI-Agent", lifespan=lifespan)

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

# Serve Frontend Static Files
current_file_dir = os.path.dirname(os.path.abspath(__file__)) # /app/backend/app
backend_dir = os.path.dirname(current_file_dir) # /app/backend
project_root = os.path.dirname(backend_dir) # /app

frontend_dist = os.path.join(project_root, "frontend/dist")

# Try to find frontend_dist in likely locations
if not os.path.exists(frontend_dist):
    frontend_dist_local = os.path.join(backend_dir, "../frontend/dist")
    if os.path.exists(frontend_dist_local):
        frontend_dist = frontend_dist_local

if os.path.exists(frontend_dist):
    # 1. Mount /assets specifically
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # 2. Catch-all route (must be last)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Protected file serving (prevent path traversal)
        safe_path = os.path.normpath(os.path.join(frontend_dist, full_path))
        if not safe_path.startswith(frontend_dist):
            # If attempt to access outside, return index.html (or could be 404/403)
            return FileResponse(os.path.join(frontend_dist, "index.html"))

        # If file exists, serve it (e.g. favicon.ico, manifest.json in root)
        if os.path.exists(safe_path) and os.path.isfile(safe_path):
            return FileResponse(safe_path)

        # Otherwise serve index.html (SPA Fallback)
        return FileResponse(os.path.join(frontend_dist, "index.html"))

else:
    @app.get("/")
    async def root():
        return {"message": "Centras AI-Agent Backend is running. Frontend not found (dev mode)."}
