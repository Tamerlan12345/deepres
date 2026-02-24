import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Report, ReportStatus
from app.config import settings
from app.prompts import SYSTEM_PROMPT
from google import genai
from google.genai import types

async def append_log(db, report_id, message, stage="processing"):
    """
    Appends a log entry to the report's logs field.
    Note: SQLite specific behavior for JSON updates might require a full replace or specific operators.
    For simplicity and compatibility, we'll read, append, and update.
    """
    try:
        # Fetch report again to ensure we have the latest data
        # In a real async environment with frequent updates, we'd need to be careful about race conditions.
        # For this task, simple read-modify-write is likely sufficient given single worker per report.
        report = await db.get(Report, report_id)
        if report:
            current_logs = list(report.logs) if report.logs else []
            new_log = {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "message": message,
                "stage": stage
            }
            current_logs.append(new_log)
            report.logs = current_logs
            await db.commit()
    except Exception as e:
        # Log error to console but don't break the main process
        print(f"Error appending log for report {report_id}: {e}")

async def process_report(report_id: int, db_session_factory):
    """
    Background task to process the report request using Gemini Deep Research (or simulated via tools).
    """
    async with db_session_factory() as db:
        report = await db.get(Report, report_id)
        if not report:
            return

        report.status = ReportStatus.PROCESSING
        await db.commit()

        await append_log(db, report_id, f"Начинаю анализ запроса: {report.query}", "starting")

        try:
            # 1. Prepare Prompt
            user_query = report.query

            # 2. Configure Gemini
            if settings.GEMINI_API_KEY == "dummy_key":
                await append_log(db, report_id, "Использую тестовый режим (Dummy Key).", "searching")

                # Mock response for dev/test without key
                await asyncio.sleep(2)
                await append_log(db, report_id, "Сформирован поисковый запрос...", "searching")

                await asyncio.sleep(2)
                await append_log(db, report_id, "Найдены релевантные источники. Читаю...", "reading")

                await asyncio.sleep(2)
                await append_log(db, report_id, "Анализирую полученные данные...", "thinking")

                response_text = """
## Анализ рынка автострахования

По результатам анализа, компания Freedom Finance демонстрирует агрессивный рост.

### Ключевые показатели

*   **Доля рынка**: Рост на 2% за последний квартал.
*   **Объем премий**: Увеличение до 15 млрд тенге.

### Визуализация данных

Вот сравнение долей рынка основных игроков:

```json:chart
{
  "type": "bar",
  "title": "Доля рынка (Mock)",
  "data": [
    {"name": "Freedom", "value": 30},
    {"name": "Eurasia", "value": 25},
    {"name": "Halyk", "value": 20},
    {"name": "Centras", "value": 15},
    {"name": "Others", "value": 10}
  ]
}
```

### Процесс оформления полиса

Процесс цифрового оформления выглядит следующим образом:

```mermaid
graph TD;
    A[Клиент] -->|Заявка| B(Сайт);
    B --> C{Проверка};
    C -->|ОК| D[Выписка полиса];
    C -->|Отказ| E[Уведомление];
```
"""
            else:
                client = genai.Client(
                    api_key=settings.GEMINI_API_KEY,
                    http_options=types.HttpOptions(api_version='v1alpha')
                )

                # Configuration for "Deep Research" behavior
                agent_name = "deep-research-pro-preview-12-2025"

                # Combined input: System Prompt + User Query
                combined_input = f"{SYSTEM_PROMPT}\n\nUSER QUERY:\n{user_query}"

                # Call interactions.create asynchronously
                # Using client.aio.interactions.create for agent interactions
                print(f"Starting Deep Research interaction for report {report_id}...")
                await append_log(db, report_id, "Запуск Deep Research агента...", "searching")

                interaction = await client.aio.interactions.create(
                    agent=agent_name,
                    input=combined_input,
                    background=True
                )

                print(f"Deep Research started. Interaction ID: {interaction.id}")
                await append_log(db, report_id, "Агент запущен. Ожидание результатов...", "searching")

                # Polling loop
                start_time = asyncio.get_running_loop().time()
                timeout = 600  # 10 minutes timeout as per requirements
                last_log_time = 0

                while True:
                    current_time = asyncio.get_running_loop().time()
                    if current_time - start_time > timeout:
                        raise TimeoutError("Deep Research timed out.")

                    await asyncio.sleep(10)

                    try:
                        # Check status
                        interaction = await client.aio.interactions.get(id=interaction.id)
                    except Exception as e:
                        # Log error but don't crash unless it's the timeout or fatal
                        # If it's a transient network error, we retry next loop
                        print(f"Warning: Error during polling for report {report_id}: {e}. Retrying...")
                        import traceback
                        traceback.print_exc()
                        await append_log(db, report_id, f"Ошибка связи с API, повторная попытка... ({e})", "retrying")
                        continue

                    # Check 'state' (standard) or 'status' (fallback/user specified)
                    status = getattr(interaction, 'state', None)
                    if status is None:
                        status = getattr(interaction, 'status', None)

                    status_str = str(status).upper()

                    # Periodic log update to keep frontend alive
                    if current_time - last_log_time > 20: # Log every 20s approx
                         await append_log(db, report_id, f"Статус обработки: {status_str}...", "processing")
                         last_log_time = current_time

                    if "PROCESSING" in status_str or "PENDING" in status_str:
                        continue
                    elif "SUCCEEDED" in status_str or "COMPLETED" in status_str:
                        await append_log(db, report_id, "Обработка завершена успешно. Формирование отчета...", "finished")
                        break
                    elif "FAILED" in status_str:
                        raise Exception(f"Deep Research failed with status: {status_str}")
                    else:
                        print(f"Unknown status {status_str}, continuing...")
                        await append_log(db, report_id, f"Неизвестный статус: {status_str}. Детали: {str(interaction)}", "unknown_status")

                # Extract result
                if not interaction.outputs:
                    raise Exception("Deep Research completed but returned no outputs.")

                # Get the last output as per instructions
                output = interaction.outputs[-1]

                try:
                    response_text = output.content.parts[0].text
                except (AttributeError, IndexError) as e:
                    print(f"Warning: Failed to access content.parts[0].text: {e}. Trying fallback.")
                    try:
                        response_text = output.text
                    except AttributeError:
                        print("Warning: Failed to access output.text. Dumping output.")
                        response_text = str(output)

                if not response_text:
                    error_msg = "Model returned empty response."
                    print(f"Error processing report {report_id}: {error_msg}")
                    await append_log(db, report_id, f"Ошибка: {error_msg}", "failed")
                    report.status = ReportStatus.FAILED
                    report.result_json = {"error": error_msg}
                    await db.commit()
                    return

            # 3. Store Result
            # Store the markdown text inside a JSON wrapper to satisfy the DB schema (JSON column)
            result_json = {"markdown": response_text}

            # 4. Save Result
            report.result_json = result_json
            report.status = ReportStatus.COMPLETED
            await db.commit()

        except Exception as e:
            # Log error
            print(f"Error processing report {report_id}: {e}")
            await append_log(db, report_id, f"Критическая ошибка: {str(e)}", "failed")
            report.status = ReportStatus.FAILED
            report.result_json = {"error": str(e)}
            await db.commit()
