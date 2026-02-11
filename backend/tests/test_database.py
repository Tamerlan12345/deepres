import unittest
import os
import sys

# Add backend directory to sys.path if running from tests directory or root
# Assumes test is run as: cd backend && python3 -m unittest tests/test_database.py
sys.path.append(os.getcwd())

from app.database import get_async_database_url

class TestDatabaseUrl(unittest.TestCase):
    def test_postgres_protocol(self):
        """Test replacement of 'postgres://' with 'postgresql+asyncpg://'"""
        original_url = "postgres://user:pass@localhost:5432/dbname"
        expected_url = "postgresql+asyncpg://user:pass@localhost:5432/dbname"
        self.assertEqual(get_async_database_url(original_url), expected_url)

    def test_postgresql_protocol_without_asyncpg(self):
        """Test replacement of 'postgresql://' with 'postgresql+asyncpg://' when asyncpg is missing"""
        original_url = "postgresql://user:pass@localhost:5432/dbname"
        expected_url = "postgresql+asyncpg://user:pass@localhost:5432/dbname"
        self.assertEqual(get_async_database_url(original_url), expected_url)

    def test_postgresql_protocol_with_asyncpg(self):
        """Test that 'postgresql+asyncpg://' is unchanged"""
        original_url = "postgresql+asyncpg://user:pass@localhost:5432/dbname"
        self.assertEqual(get_async_database_url(original_url), original_url)

    def test_other_protocol_sqlite(self):
        """Test that 'sqlite://' is unchanged"""
        original_url = "sqlite:///./test.db"
        self.assertEqual(get_async_database_url(original_url), original_url)

    def test_other_protocol_mysql(self):
        """Test that 'mysql://' is unchanged"""
        original_url = "mysql://user:pass@localhost:3306/dbname"
        self.assertEqual(get_async_database_url(original_url), original_url)

    def test_postgresql_in_middle_of_string(self):
        """Test that 'postgresql://' logic doesn't trigger if it's not the start"""
        # Although the logic is `startswith`, it's good to confirm.
        original_url = "some-scheme://postgresql://something"
        self.assertEqual(get_async_database_url(original_url), original_url)

    def test_empty_string(self):
        """Test empty string returns empty string"""
        self.assertEqual(get_async_database_url(""), "")

if __name__ == "__main__":
    unittest.main()
