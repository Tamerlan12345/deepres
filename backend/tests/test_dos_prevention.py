import unittest
from app.api import UserLogin, ReportCreate
from pydantic import ValidationError

class TestDoSPrevention(unittest.TestCase):
    def test_user_login_max_length(self):
        with self.assertRaises(ValidationError):
            UserLogin(username="a" * 101, password="password")

        with self.assertRaises(ValidationError):
            UserLogin(username="admin", password="a" * 129)

        # Should pass
        UserLogin(username="a" * 100, password="a" * 128)

    def test_report_create_max_length(self):
        with self.assertRaises(ValidationError):
            ReportCreate(query="a" * 2001)

        # Should pass
        ReportCreate(query="a" * 2000)

if __name__ == '__main__':
    unittest.main()
