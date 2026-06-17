from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router
from app.database import engine, Base, AsyncSessionLocal
from app.models import User
from app.auth import get_password_hash
from sqlalchemy import select
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import secrets
import string

app = FastAPI(title="Deep Research Agent API")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to create DB and default Admin
@app.on_event("startup")
async def startup_event():
    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Проверяем/Создаем Админа
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        admin_user = result.scalars().first()

        if not admin_user:
            print("Creating default admin user...")

            admin_password = os.environ.get("ADMIN_PASSWORD")
            if not admin_password:
                alphabet = string.ascii_letters + string.digits
                admin_password = ''.join(secrets.choice(alphabet) for i in range(16))
                print(f"WARNING: Generated random admin password: {admin_password}")
                print("Please change it immediately or set ADMIN_PASSWORD environment variable.")
            else:
                print("Using provided ADMIN_PASSWORD.")

            hashed_pw = get_password_hash(admin_password)
            new_admin = User(username="admin", hashed_password=hashed_pw, admin="yes")
            session.add(new_admin)
            await session.commit()
            print(f"Admin user created (login: admin).")
        else:
            # Убедимся, что у существующего админа права yes (если бд была мигрирована)
            if admin_user.admin != "yes":
                admin_user.admin = "yes"
                await session.commit()

app.include_router(router, prefix="/api")

# Serve Frontend Static Files (Preserved from original implementation)
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
        safe_path = os.path.abspath(os.path.join(frontend_dist, full_path))
        abs_frontend_dist = os.path.abspath(frontend_dist)
        try:
            # os.path.commonpath prevents partial path traversal (e.g. dist-secret bypassing dist check)
            if os.path.commonpath([abs_frontend_dist, safe_path]) != abs_frontend_dist:
                return FileResponse(os.path.join(frontend_dist, "index.html"))
        except ValueError:
            # Occurs if paths are on different drives (Windows edge case)
            return FileResponse(os.path.join(frontend_dist, "index.html"))

        if os.path.exists(safe_path) and os.path.isfile(safe_path):
            return FileResponse(safe_path)

        return FileResponse(os.path.join(frontend_dist, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
