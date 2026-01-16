import unittest
import sys
import os

# Add the 'app' folder to sys.path so imports work correctly
sys.path.append(os.path.join(os.getcwd(), 'app'))

# Fix the path to credentials for test if running from root
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(os.getcwd(), 'credentials', 'service-account.json')

from src import create_app
from src.db_firestore import update_config

class SettingsTemplateTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_settings_page_renders_with_pin_last_rotate(self):
        """Tests if the settings page renders correctly when pin_last_rotate is set."""
        from datetime import datetime
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 'test_admin'
            sess['user_role'] = 'admin'
            sess['is_admin'] = True

        # Simulate config data. Since get_config retrieves from Firestore,
        # and we don't want to modify the real database in tests (unless we have an emulator),
        # we'll try to use a mock or just check if the hasattr error occurs.
        # In this project, tests seem to use real Firestore (looking at test_pin_access.py).
        
        # Set pin_last_rotate as datetime
        with self.app.app_context():
            from src.db_firestore import _warsaw_now
            update_config(pin_last_rotate=_warsaw_now())

        response = self.client.get('/admin/settings')
        self.assertEqual(response.status_code, 200)
        # If hasattr is undefined, it will throw 500 and the test will fail (or return 500)
        
    def test_settings_page_renders_with_string_pin_last_rotate(self):
        """Tests if the settings page renders correctly when pin_last_rotate is a string."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 'test_admin'
            sess['user_role'] = 'admin'
            sess['is_admin'] = True

        with self.app.app_context():
            update_config(pin_last_rotate="2026-01-15 12:00:00")

        response = self.client.get('/admin/settings')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
