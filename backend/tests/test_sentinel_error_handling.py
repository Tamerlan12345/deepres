
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.api import get_current_user
from app.models import User

class TestSentinelErrorHandling(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

        # Mock current user to bypass authentication
        self.mock_user = User(id=1, username="testuser", admin="no")
        app.dependency_overrides[get_current_user] = lambda: self.mock_user

    def tearDown(self):
        app.dependency_overrides = {}

    def test_list_reports_error_leakage(self):
        # Mock DB session to raise an exception
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("LEAKED_DATABASE_SECRET")

        async def override_get_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_get_db

        response = self.client.get("/api/reports")

        # Verify the fix: The error message IS NOT exposed
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("LEAKED_DATABASE_SECRET", response.text)
        self.assertIn("An internal error occurred.", response.text)

if __name__ == "__main__":
    unittest.main()
