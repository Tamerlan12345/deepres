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

class TestApiSecurity(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Override app db dependency
        import app.main
        self.app = app.main.app
        self.app.dependency_overrides[get_db] = override_get_db

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Mock app.main's engine directly for startup events
        with patch('app.main.engine', engine), patch('app.main.AsyncSessionLocal', TestingSessionLocal):
            self.client = TestClient(self.app)

        # Create users
        async with TestingSessionLocal() as db:
            owner = User(username="owner", hashed_password=get_password_hash("password"), admin="no")
            other = User(username="other", hashed_password=get_password_hash("password"), admin="no")
            admin = User(username="admin_user", hashed_password=get_password_hash("password"), admin="yes")
            db.add_all([owner, other, admin])
            await db.commit()
            await db.refresh(owner)
            await db.refresh(other)
            await db.refresh(admin)

            self.owner_id = owner.id
            self.other_id = other.id
            self.admin_id = admin.id

            # Create report
            report = Report(
                query="Test Query",
                status=ReportStatus.COMPLETED,
                id_users=self.owner_id,
                result_json={"summary": "test", "detailed_analysis": "test"},
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

    def test_export_pdf_unauthenticated(self):
        response = self.client.get(f"/api/reports/{self.report_id}/pdf")
        self.assertEqual(response.status_code, 401)

    @patch("app.api.HTML")
    def test_export_pdf_authorized_owner(self, mock_html):
        mock_html.return_value.write_pdf.return_value = b"%PDF-1.4..."
        token = self.get_token("owner", "password")
        response = self.client.get(
            f"/api/reports/{self.report_id}/pdf",
            headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(response.status_code, 200)

    @patch("app.api.HTML")
    def test_export_pdf_authorized_admin(self, mock_html):
        mock_html.return_value.write_pdf.return_value = b"%PDF-1.4..."
        token = self.get_token("admin_user", "password")
        response = self.client.get(
            f"/api/reports/{self.report_id}/pdf",
            headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(response.status_code, 200)

    def test_export_pdf_unauthorized(self):
        token = self.get_token("other", "password")
        response = self.client.get(
            f"/api/reports/{self.report_id}/pdf",
            headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(response.status_code, 403)
