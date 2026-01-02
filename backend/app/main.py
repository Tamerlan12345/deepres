from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging
from app.config import settings
from app.database import init_db, AsyncSessionLocal
from app.api import router as api_router
from app.models import User
from contextlib import asynccontextmanager
from passlib.context import CryptContext
from sqlalchemy import select

# 1. Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("app.log")]
)
logger = logging.getLogger("app")

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
    # Log DATABASE_URL (masking password)
    db_url = settings.DATABASE_URL
    if "password" in db_url:
        try:
             from urllib.parse import urlparse, urlunparse
             parsed = urlparse(db_url)
             if parsed.password:
                 # replace password with ****
                 netloc = parsed.netloc.replace(f":{parsed.password}@", ":****@")
                 masked_url = urlunparse(parsed._replace(netloc=netloc))
             else:
                 masked_url = db_url
        except Exception:
             masked_url = "Could not parse URL safely"
    else:
        masked_url = db_url

    logger.info(f"Starting application with DATABASE_URL: {masked_url}")

    # Initialize DB tables
    await init_db()

    # Create Admin User
    await create_admin_user()

    yield

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

if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
else:
    # Fallback for local development if run from backend root
    frontend_dist_local = os.path.join(backend_dir, "../frontend/dist")
    if os.path.exists(frontend_dist_local):
         app.mount("/", StaticFiles(directory=frontend_dist_local, html=True), name="frontend")
    else:
        @app.get("/")
        async def root():
            return {"message": "Centras AI-Agent Backend is running. Frontend not found (dev mode)."}
