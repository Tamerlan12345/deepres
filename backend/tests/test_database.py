import uuid
import unittest
import os
import sys
from unittest.mock import patch, AsyncMock

# Add backend directory to sys.path if running from tests directory or root
# Assumes test is run as: cd backend && python3 -m unittest tests/test_database.py
sys.path.append(os.getcwd())

from app.database import get_async_database_url, init_db

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

class TestInitDB(unittest.IsolatedAsyncioTestCase):
    async def test_init_db_reset_true(self):
        """Test that drop_all is called when RESET_DB is True"""
        with patch("app.database.settings") as mock_settings, \
             patch("app.database.engine") as mock_engine, \
             patch("app.database.Base") as mock_base:

            mock_settings.RESET_DB = True

            # Mock engine.begin() context manager
            mock_conn = AsyncMock()
            # engine.begin() returns an async context manager, so we mock __aenter__
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn

            await init_db()

            # Verify drop_all was called via run_sync
            mock_conn.run_sync.assert_any_call(mock_base.metadata.drop_all)
            # Verify create_all was also called
            mock_conn.run_sync.assert_any_call(mock_base.metadata.create_all)

    async def test_init_db_reset_false(self):
        """Test that drop_all is NOT called when RESET_DB is False"""
        with patch("app.database.settings") as mock_settings, \
             patch("app.database.engine") as mock_engine, \
             patch("app.database.Base") as mock_base:

            mock_settings.RESET_DB = False

            mock_conn = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn

            await init_db()

            # Verify drop_all was NOT called
            # Iterate over calls to run_sync to ensure drop_all was not one of them
            for call in mock_conn.run_sync.call_args_list:
                args, _ = call
                self.assertNotEqual(args[0], mock_base.metadata.drop_all, "drop_all should not be called")

            # Verify create_all was called
            mock_conn.run_sync.assert_called_with(mock_base.metadata.create_all)

if __name__ == "__main__":
    unittest.main()
