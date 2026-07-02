import unittest
import json
import uuid
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.models import Report, ReportStatus, User
from app.auth import get_password_hash
from datetime import datetime, timezone

SQLALCHEMY_DATABASE_URL = f"sqlite+aiosqlite:///:memory:?cache=shared&v={uuid.uuid4().hex}"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

import app.database
app.database.engine = engine
app.database.AsyncSessionLocal = TestingSessionLocal

from app.main import app
app.dependency_overrides[get_db] = lambda: TestingSessionLocal()

class TestXSSPrevention(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Create admin user to access the endpoint securely
        async with TestingSessionLocal() as db:
            admin_user = User(username="testuser", hashed_password=get_password_hash("password"), admin="yes")
            db.add(admin_user)
            await db.commit()
            await db.refresh(admin_user)
            self.user_id = admin_user.id

            # The malicious payload mimicking XSS in Mermaid diagram definition
            malicious_payload = "A <script>alert(1)</script> B & \" '"

            report = Report(
                query="test query",
                status=ReportStatus.COMPLETED,
                id_users=self.user_id,
                result_json={"summary": malicious_payload, "detailed_analysis": malicious_payload},
                created_at=datetime.now(timezone.utc)
            )
            db.add(report)
            await db.commit()
            await db.refresh(report)
            self.report_id = report.id

    async def asyncTearDown(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def test_export_pdf_xss_prevention(self):
        from httpx import AsyncClient, ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/login", json={"username": "testuser", "password": "password"})
            token = response.json()["access_token"]

            with patch("app.api.HTML") as mock_html:
                mock_html.return_value.write_pdf.return_value = b"%PDF-1.4..."

                response = await client.get(
                    f"/api/reports/{self.report_id}/pdf",
                    headers={"Authorization": f"Bearer {token}"}
                )

                self.assertEqual(response.status_code, 200)

                # Check what was passed to HTML
                mock_html.assert_called_once()
                args, kwargs = mock_html.call_args
                html_string = kwargs.get('string', args[0] if args else '')

                # XSS Payload should be escaped
                self.assertNotIn("<script>", html_string)
                self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html_string)

if __name__ == "__main__":
    unittest.main()
