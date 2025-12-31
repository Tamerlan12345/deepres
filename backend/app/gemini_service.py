import json
import asyncio
from sqlalchemy.orm import Session
from app.models import Report, ReportStatus
from app.config import settings
from app.prompts import SYSTEM_PROMPT
from google import genai
from google.genai import types

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

        try:
            # 1. Prepare Prompt
            user_query = report.query

            # 2. Configure Gemini
            if settings.GEMINI_API_KEY == "dummy_key":
                # Mock response for dev/test without key
                await asyncio.sleep(3) # Simulate thinking
                response_text = """
```json
{
  "summary": "MOCK RESULT: Deep Research simulated. Freedom Finance is aggressively expanding in auto insurance.",
  "key_metrics": [
    {"label": "Simulated Market Share", "value": "10%", "change": "+2%"}
  ],
  "charts_data": [],
  "detailed_analysis": "## Deep Research Simulation\\n\\nSince no API key was provided, this is a simulated response demonstrating the flow.\\n\\n1. **Step 1**: Analyzed query.\\n2. **Step 2**: 'Searched' Google.\\n3. **Step 3**: Synthesized results.",
  "sources": ["http://mock-source.com"]
}
```
"""
            else:
                client = genai.Client(
                    api_key=settings.GEMINI_API_KEY,
                    http_options=types.HttpOptions(api_version='v1alpha')
                )

                # Configuration for "Deep Research" behavior
                model_name = "deep-research-pro-preview-12-2025"

                # Grounding (Google Search Tool)
                google_search_tool = types.Tool(
                    google_search=types.GoogleSearch()
                )

                # Call generate_content asynchronously
                # Using client.aio.models.generate_content for true async support
                response = await client.aio.models.generate_content(
                    model=model_name,
                    contents=user_query,
                    config=types.GenerateContentConfig(
                        tools=[google_search_tool],
                        system_instruction=SYSTEM_PROMPT
                    )
                )

                # Log grounding metadata for debugging/monitoring
                if response.candidates and response.candidates[0].grounding_metadata:
                    print(f"Grounding Metadata: {response.candidates[0].grounding_metadata}")

                if not response.text:
                     # Handle safety filters or empty responses
                     error_msg = "Model returned empty response. Likely triggered safety filters or no information found."
                     print(f"Error processing report {report_id}: {error_msg}")
                     report.status = ReportStatus.FAILED
                     report.result_json = {"error": error_msg}
                     await db.commit()
                     return

                response_text = response.text

            # 3. Parse JSON
            # Clean up potential markdown formatting
            json_str = response_text.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            elif json_str.startswith("```"): # handle case where language isn't specified
                json_str = json_str[3:]

            if json_str.endswith("```"):
                json_str = json_str[:-3]

            json_str = json_str.strip()

            try:
                result_json = json.loads(json_str)
            except json.JSONDecodeError:
                # Fallback: Model might have returned just text despite instructions.
                # Create a wrapper.
                result_json = {
                    "summary": "Model output was not strict JSON. See detailed analysis.",
                    "key_metrics": [],
                    "charts_data": [],
                    "detailed_analysis": response_text,
                    "sources": []
                }

            # 4. Save Result
            report.result_json = result_json
            report.status = ReportStatus.COMPLETED
            await db.commit()

        except Exception as e:
            # Log error
            print(f"Error processing report {report_id}: {e}")
            report.status = ReportStatus.FAILED
            report.result_json = {"error": str(e)}
            await db.commit()
