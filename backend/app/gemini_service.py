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
                agent_name = "deep-research-pro-preview-12-2025"

                # Combined input: System Prompt + User Query
                combined_input = f"{SYSTEM_PROMPT}\n\nUSER QUERY:\n{user_query}"

                # Call interactions.create asynchronously
                # Using client.aio.interactions.create for agent interactions
                print(f"Starting Deep Research interaction for report {report_id}...")
                interaction = await client.aio.interactions.create(
                    agent=agent_name,
                    input=combined_input,
                    background=True
                )

                print(f"Deep Research started. Interaction Name (ID): {interaction.name}")

                # Polling loop
                start_time = asyncio.get_running_loop().time()
                timeout = 600  # 10 minutes timeout as per requirements

                while True:
                    current_time = asyncio.get_running_loop().time()
                    if current_time - start_time > timeout:
                        raise TimeoutError("Deep Research timed out.")

                    await asyncio.sleep(10)

                    try:
                        # Check status
                        interaction = await client.aio.interactions.get(id=interaction.name)
                    except Exception as e:
                        # Log error but don't crash unless it's the timeout or fatal
                        # If it's a transient network error, we retry next loop
                        print(f"Warning: Error during polling for report {report_id}: {e}. Retrying...")
                        continue

                    # Check 'state' (standard) or 'status' (fallback/user specified)
                    status = getattr(interaction, 'state', None)
                    if status is None:
                        status = getattr(interaction, 'status', None)

                    status_str = str(status).upper()

                    if "PROCESSING" in status_str or "PENDING" in status_str:
                        continue
                    elif "SUCCEEDED" in status_str or "COMPLETED" in status_str:
                        break
                    elif "FAILED" in status_str:
                        raise Exception(f"Deep Research failed with status: {status_str}")
                    else:
                        print(f"Unknown status {status_str}, continuing...")

                # Extract result
                if not interaction.outputs:
                    raise Exception("Deep Research completed but returned no outputs.")

                # Get the last output as per instructions
                output = interaction.outputs[-1]

                try:
                    response_text = output.content.parts[0].text
                except (AttributeError, IndexError) as e:
                    print(f"Warning: Failed to access content.parts[0].text: {e}. Dumping output.")
                    response_text = str(output)

                if not response_text:
                    error_msg = "Model returned empty response."
                    print(f"Error processing report {report_id}: {error_msg}")
                    report.status = ReportStatus.FAILED
                    report.result_json = {"error": error_msg}
                    await db.commit()
                    return

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
