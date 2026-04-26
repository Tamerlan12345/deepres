import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.models import User, Report, ReportStatus
from app.auth import get_password_hash
from datetime import datetime, timezone
import uuid
import html

SQLALCHEMY_DATABASE_URL = f"sqlite+aiosqlite:///:memory:?cache=shared&v={uuid.uuid4().hex}"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

class TestXSSPrevention(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        import app.main
        self.app = app.main.app
        self.app.dependency_overrides[get_db] = override_get_db

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        with patch('app.main.engine', engine), patch('app.main.AsyncSessionLocal', TestingSessionLocal):
            self.client = TestClient(self.app)

        # Create user
        async with TestingSessionLocal() as db:
            user = User(username="testuser", hashed_password=get_password_hash("password"), admin="no")
            db.add(user)
            await db.commit()
            await db.refresh(user)
            self.user_id = user.id

            # Create report with malicious content
            self.malicious_query = "<script>alert('XSS')</script>"
            self.malicious_summary = "<b>Bold</b> & <script>evil()</script>"
            self.malicious_analysis = "<i>Italic</i> \"quote\""

            report = Report(
                query=self.malicious_query,
                status=ReportStatus.COMPLETED,
                id_users=self.user_id,
                result_json={
                    "summary": self.malicious_summary,
                    "detailed_analysis": self.malicious_analysis
                },
                created_at=datetime.now(timezone.utc)
            )
            db.add(report)
            await db.commit()
            await db.refresh(report)
            self.report_id = report.id

    async def asyncTearDown(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        self.app.dependency_overrides.clear()

    def get_token(self, username, password):
        response = self.client.post("/api/login", json={"username": username, "password": password})
        return response.json()["access_token"]

    def test_export_pdf_xss_prevention(self):
        token = self.get_token("testuser", "password")

        # Mock HTML class from weasyprint to capture the HTML string
        with patch("app.api.HTML") as mock_html:
            mock_html.return_value.write_pdf.return_value = b"%PDF-1.4..."

            response = self.client.get(
                f"/api/reports/{self.report_id}/pdf",
                headers={"Authorization": f"Bearer {token}"}
            )

            self.assertEqual(response.status_code, 200)

            call_args = mock_html.call_args
            if 'string' in call_args.kwargs:
                html_content = call_args.kwargs['string']
            else:
                html_content = call_args[0][0] if call_args[0] else ""

            self.assertNotIn("<script>", html_content, "Raw <script> tag found in PDF HTML!")
            self.assertIn("&lt;script&gt;", html_content, "Escaped <script> tag not found!")

            self.assertIn("&amp;", html_content, "Ampersand not escaped!")
            self.assertIn("&quot;", html_content, "Quote not escaped!")
