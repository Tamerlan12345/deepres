from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db, AsyncSessionLocal
from app.models import Report, ReportStatus
from app.gemini_service import process_report
from pydantic import BaseModel
from typing import Optional, List
import logging

# Настройка простого логгера
logger = logging.getLogger("uvicorn")

router = APIRouter()

class ReportCreate(BaseModel):
    query: str

class ReportResponse(BaseModel):
    id: int
    query: str
    status: str
    logs: Optional[List[dict]] = []
    result_json: Optional[dict] = None
    created_at: str

    class Config:
        from_attributes = True

@router.post("/reports", response_model=ReportResponse)
async def create_report(report_in: ReportCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    report = Report(query=report_in.query, status=ReportStatus.PENDING)
    db.add(report)
    await db.commit()
    await db.refresh(report)

    # Pass session factory instead of session because the session might be closed
    background_tasks.add_task(process_report, report.id, AsyncSessionLocal)

    return ReportResponse(
        id=report.id,
        query=report.query,
        status=report.status,
        logs=report.logs,
        created_at=report.created_at.isoformat()
    )

@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.get(Report, report_id)
    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportResponse(
        id=result.id,
        query=result.query,
        status=result.status,
        logs=result.logs,
        result_json=result.result_json,
        created_at=result.created_at.isoformat()
    )

@router.get("/reports", response_model=List[ReportResponse])
async def list_reports(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    try:
        # 1. Проверяем запрос к БД
        query = select(Report).order_by(Report.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        reports = result.scalars().all()

        logger.info(f"Найдено отчетов в БД: {len(reports)}") # Лог в консоль

        # 2. Проверяем сборку ответа
        response = []
        for r in reports:
            response.append(ReportResponse(
                id=r.id,
                query=r.query,
                status=r.status,
                logs=r.logs,
                result_json=r.result_json,
                # Добавляем защиту, если вдруг created_at отсутствует
                created_at=r.created_at.isoformat() if r.created_at else ""
            ))
        return response

    except Exception as e:
        logger.error(f"ОШИБКА при получении истории: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

from fastapi.responses import Response
from weasyprint import HTML, CSS

@router.get("/reports/{report_id}/pdf")
async def export_pdf(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.get(Report, report_id)
    if not result or not result.result_json:
        raise HTTPException(status_code=404, detail="Report or data not found")

    data = result.result_json

    # Simple HTML generation
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
        <p><strong>Query:</strong> {result.query}</p>
        <p><strong>Date:</strong> {result.created_at.strftime("%Y-%m-%d %H:%M")}</p>

        <div class="summary">
            <h3>Executive Summary</h3>
            <p>{data.get('summary', 'No summary available.')}</p>
        </div>

        <div class="metrics">
            <h3>Key Metrics</h3>
            {''.join([f'<div class="metric">{m.get("label")}: <span class="value">{m.get("value")}</span> ({m.get("change", "")} {m.get("trend", "")})</div>' for m in data.get('key_metrics', [])])}
        </div>

        <div class="analysis">
            <h3>Detailed Analysis</h3>
            <div style="white-space: pre-wrap;">{data.get('detailed_analysis', '')}</div>
        </div>

        <div class="sources">
            <h4>Sources</h4>
            <ul>
                {''.join([f'<li>{s}</li>' for s in data.get('sources', [])])}
            </ul>
        </div>
    </body>
    </html>
    """

    pdf_bytes = HTML(string=html_content).write_pdf()

    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=report_{report_id}.pdf"})
