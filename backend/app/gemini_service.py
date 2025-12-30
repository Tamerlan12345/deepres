import json
import re
import asyncio
from sqlalchemy.orm import Session
from app.models import Report, ReportStatus
from app.config import settings
from app.prompts import SYSTEM_PROMPT
import google.generativeai as genai

async def process_report(report_id: int, db_session_factory):
    """
    Background task to process the report request.
    """
    async with db_session_factory() as db:
        report = await db.get(Report, report_id)
        if not report:
            return

        report.status = ReportStatus.PROCESSING
        await db.commit()

        try:
            # 1. Prepare Prompt
            full_prompt = f"{SYSTEM_PROMPT}\n\nUSER REQUEST: {report.query}"

            # 2. Call Gemini
            response_text = ""
            if settings.GEMINI_API_KEY == "dummy_key":
                # Mock response
                await asyncio.sleep(5) # Simulate delay
                response_text = """
```json
{
  "summary": "Анализ показывает, что Freedom Finance активно наращивает долю в онлайн-страховании, в то время как Centras сохраняет стабильные позиции в корпоративном секторе. Основной тренд — цифровизация урегулирования убытков.",
  "key_metrics": [
    {"label": "Доля рынка Сентрас", "value": "4.2%", "change": "+0.5%"},
    {"label": "Лидер роста", "value": "Freedom Insurance", "trend": "Рост"}
  ],
  "charts_data": [
    {
       "type": "bar",
       "title": "Сравнение GWP (млн тенге) Q3 2024",
       "labels": ["Centras", "Freedom", "Halyk", "Eurasia"],
       "datasets": [{"label": "GWP", "data": [12500, 24000, 45000, 52000]}]
    }
  ],
  "detailed_analysis": "## Обзор рынка\\nРынок страхования демонстрирует рост на 15% г/г.\\n\\n### Конкуренты\\n**Freedom Insurance** делает ставку на экосистему и автострахование.\\n**Halyk** доминирует за счет банковского канала.\\n\\n### Позиции Centras\\nСентрас силен в сервисном подходе (SOS) и корпоративном ДМС.",
  "sources": ["https://kase.kz", "https://nationalbank.kz"]
}
```
"""
            else:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                # Use gemini-1.5-flash or pro for better performance/cost balance if available,
                # or the specific 'deep-research' if it corresponds to a model name.
                # For now using 'gemini-1.5-pro-latest' as a safe bet for complex tasks.
                model = genai.GenerativeModel('gemini-1.5-pro-latest')
                response = model.generate_content(full_prompt)
                response_text = response.text

            # 3. Parse JSON
            # Remove markdown fences if present
            json_str = response_text.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]

            try:
                result_json = json.loads(json_str)
            except json.JSONDecodeError:
                # Fallback if JSON is malformed
                result_json = {
                    "summary": "Error parsing JSON response from model.",
                    "raw_response": response_text
                }

            # 4. Save Result
            report.result_json = result_json
            report.status = ReportStatus.COMPLETED
            await db.commit()

        except Exception as e:
            report.status = ReportStatus.FAILED
            report.result_json = {"error": str(e)}
            await db.commit()
