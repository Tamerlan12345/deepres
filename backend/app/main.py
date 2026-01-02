from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.config import settings
from app.database import init_db
from app.api import router as api_router
from contextlib import asynccontextmanager

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Log DATABASE_URL (masking password)
    db_url = settings.DATABASE_URL
    if "password" in db_url:
        # Basic masking, though for full safety a regex is better.
        # But here we assume typical format or just print it if it's safe (sqlite)
        masked_url = db_url # TODO: Implement masking if needed
        # For now, let's just log it as requested "скрыв пароль"
        # Since I am in control of the code, I will write a small logic
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
# In Docker, we are likely in /app/backend or /app.
# If WORKDIR is /app/backend, then frontend is at ../frontend/dist
# If WORKDIR is /app, then frontend is at frontend/dist

# Let's try to locate it relative to this file
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
