from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.database import get_db, AsyncSessionLocal
from app.models import Report, ReportStatus, User
from app.gemini_service import process_report
from app.auth import verify_password, create_access_token, get_password_hash
from app.config import settings
from datetime import timedelta
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
from jose import JWTError, jwt
import html

# Настройка логгера
logger = logging.getLogger("uvicorn")

router = APIRouter()

# Схема для токена (указываем URL логина, хотя используем JSON body)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

class UserLogin(BaseModel):
    username: str = Field(..., max_length=50)
    password: str = Field(..., max_length=128)

class Token(BaseModel):
    access_token: str
    token_type: str
    admin: str  # Возвращаем статус админа

class ReportCreate(BaseModel):
    query: str = Field(..., max_length=5000)

class ReportResponse(BaseModel):
    id: int
    query: str
    status: str
    logs: Optional[List[dict]] = []
    result_json: Optional[dict] = None
    created_at: str

    class Config:
        from_attributes = True

# --- АВТОРИЗАЦИЯ ---

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # Возвращаем admin статус, чтобы фронтенд знал, показывать ли кнопку
    return {"access_token": access_token, "token_type": "bearer", "admin": user.admin}

# --- УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ (ТОЛЬКО АДМИН) ---

@router.post("/admin/users", status_code=201)
async def create_user(
    new_user: UserLogin,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.admin != "yes":
        raise HTTPException(status_code=403, detail="Not authorized. Admin access required.")

    # Проверка на существование
    existing = await db.execute(select(User).where(User.username == new_user.username))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_pw = get_password_hash(new_user.password)
    # Создаем обычного пользователя (admin="no")
    user_db = User(username=new_user.username, hashed_password=hashed_pw, admin="no")
    db.add(user_db)
    await db.commit()
    return {"message": f"User {new_user.username} created successfully"}

# --- ОТЧЕТЫ ---

@router.post("/reports", response_model=ReportResponse)
async def create_report(
    report_in: ReportCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Привязываем отчет к ID текущего пользователя
    report = Report(
        query=report_in.query,
        status=ReportStatus.PENDING,
        id_users=current_user.id
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    background_tasks.add_task(process_report, report.id, AsyncSessionLocal)

    return ReportResponse(
        id=report.id,
        query=report.query,
        status=report.status,
        logs=report.logs,
        created_at=report.created_at.isoformat()
    )

@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.get(Report, report_id)
    if not result:
        raise HTTPException(status_code=404, detail="Report not found")

    # Проверка прав доступа: Админ видит всё, Пользователь видит свои или общие (NULL)
    if current_user.admin != "yes" and result.id_users is not None and result.id_users != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this report")

    return ReportResponse(
        id=result.id,
        query=result.query,
        status=result.status,
        logs=result.logs,
        result_json=result.result_json,
        created_at=result.created_at.isoformat()
    )

@router.get("/reports", response_model=List[ReportResponse])
async def list_reports(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Логика фильтрации:
        # Если админ -> видит всё.
        # Если не админ -> видит (свои) ИЛИ (общие/NULL).

        query = select(Report).order_by(Report.created_at.desc()).offset(skip).limit(limit)

        if current_user.admin != "yes":
            query = query.where(
                or_(
                    Report.id_users == current_user.id,
                    Report.id_users == None
                )
            )

        result = await db.execute(query)
        reports = result.scalars().all()

        response = []
        for r in reports:
            response.append(ReportResponse(
                id=r.id,
                query=r.query,
                status=r.status,
                logs=r.logs,
                result_json=r.result_json,
                created_at=r.created_at.isoformat() if r.created_at else ""
            ))
        return response

    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred.")

# PDF экспорт (оставил как есть, добавил только получение пользователя для совместимости, но без строгой проверки пока)
from fastapi.responses import Response
from weasyprint import HTML
from starlette.concurrency import run_in_threadpool

@router.get("/reports/{report_id}/pdf")
async def export_pdf(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.get(Report, report_id)
    if not result or not result.result_json:
        raise HTTPException(status_code=404, detail="Report or data not found")

    # Access control
    if current_user.admin != "yes" and result.id_users is not None and result.id_users != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to export this report")

    # ... (код генерации PDF без изменений) ...
    data = result.result_json
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; padding: 20px; }}
            h1 {{ color: #003366; }}
            .summary {{ background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .metric {{ display: inline-block; width: 45%; margin-bottom: 10px; }}
            .value {{ font-size: 1.2em; font-weight: bold; }}
            .analysis {{ margin-top: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #003366; color: white; }}
        </style>
    </head>
    <body>
        <div style="text-align: right; color: #666;">CONFIDENTIAL - CENTRAS INSURANCE</div>
        <h1>Strategic AI Analysis Report</h1>
        <p><strong>Query:</strong> {html.escape(result.query)}</p>
        <p><strong>Date:</strong> {result.created_at.strftime("%Y-%m-%d %H:%M")}</p>

        <div class="summary">
            <h3>Executive Summary</h3>
            <p>{html.escape(data.get('summary', 'No summary available.'))}</p>
        </div>

        <div style="white-space: pre-wrap;">{html.escape(data.get('detailed_analysis', ''))}</div>
    </body>
    </html>
    """

    def _generate_pdf(html: str):
        return HTML(string=html).write_pdf()

    pdf_bytes = await run_in_threadpool(_generate_pdf, html_content)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=report_{report_id}.pdf"})
