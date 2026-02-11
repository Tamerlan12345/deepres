import unittest
import os
import sys
import importlib

# Add backend directory to sys.path if running from tests directory or root
# Assumes test is run as: cd backend && python3 -m unittest tests/test_config.py
sys.path.append(os.getcwd())

class TestConfig(unittest.TestCase):
    def setUp(self):
        # Save original env var
        self.original_secret = os.environ.get("SECRET_KEY")
        if "SECRET_KEY" in os.environ:
            del os.environ["SECRET_KEY"]

    def tearDown(self):
        # Restore original env var
        if self.original_secret:
            os.environ["SECRET_KEY"] = self.original_secret
        elif "SECRET_KEY" in os.environ:
            del os.environ["SECRET_KEY"]

    def test_secret_key_default_randomness(self):
        """Test that SECRET_KEY is random and changes if not set in env."""
        import app.config

        # Ensure env var is cleared (setup does this, but confirm)
        if "SECRET_KEY" in os.environ:
            del os.environ["SECRET_KEY"]

        # Reload to get a fresh Settings instance
        importlib.reload(app.config)
        key1 = app.config.settings.SECRET_KEY

        # It should not be empty
        self.assertTrue(len(key1) > 0)

        # Reload again -> should be different
        importlib.reload(app.config)
        key2 = app.config.settings.SECRET_KEY

        self.assertNotEqual(key1, key2, "SECRET_KEY should be random on each reload if not set")

        # It should not be the old vulnerable key
        vulnerable_key = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
        self.assertNotEqual(key1, vulnerable_key)

    def test_secret_key_from_env(self):
        """Test that SECRET_KEY respects environment variable."""
        test_val = "test_secret_key_explicit"
        os.environ["SECRET_KEY"] = test_val

        import app.config
        importlib.reload(app.config)

        self.assertEqual(app.config.settings.SECRET_KEY, test_val)

if __name__ == "__main__":
    unittest.main()
