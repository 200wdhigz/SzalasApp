import unittest
import sys
import os

# Dodaj folder 'app' do ścieżki, aby importy działały
sys.path.append(os.path.join(os.getcwd(), 'app'))

# Popraw ścieżkę do credentials dla testu, jeśli uruchamiamy z roota
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(os.getcwd(), 'credentials', 'service-account.json')

from src import create_app
from flask import url_for, session
from src.db_firestore import update_config

class SettingsPinViewTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_admin_can_see_current_pin(self):
        """Sprawdza, czy administrator widzi aktualny kod PIN na stronie ustawień."""
        test_pin = "987654"
        
        with self.app.app_context():
            update_config(view_pin=test_pin)

        with self.client.session_transaction() as sess:
            sess['user_id'] = 'test_admin'
            sess['user_role'] = 'admin'
            sess['is_admin'] = True

        response = self.client.get('/admin/settings')
        self.assertEqual(response.status_code, 200)
        
        # Obecnie PIN jest w placeholderze, co też jest "widoczne" w HTML, 
        # ale chcemy go mieć w bardziej przystępnej formie.
        # Test na razie może przejść jeśli placeholder zawiera PIN, 
        # ale my chcemy go sprawdzić w treści strony (np. w badge lub dedykowanym polu).
        html_content = response.data.decode('utf-8')
        self.assertIn(test_pin, html_content)

if __name__ == '__main__':
    unittest.main()
