import unittest
import sys
import os

# Dodaj folder 'app' do ścieżki, aby importy działały
sys.path.append(os.path.join(os.getcwd(), 'app'))

# Popraw ścieżkę do credentials dla testu, jeśli uruchamiamy z roota
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(os.getcwd(), 'credentials', 'service-account.json')

from src import create_app
from src.db_firestore import update_config
from flask import url_for, session

class PinAccessTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        
        # Ustawienie testowego PINu
        with self.app.app_context():
            update_config(view_pin='123456', pin_auto_rotate=False)

    def test_sprzet_card_redirects_to_pin(self):
        """Sprawdza, czy próba wejścia na kartę sprzętu bez logowania przekierowuje do PINu."""
        response = self.client.get('/sprzet/test_id')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/pin', response.location)

    def test_correct_pin_grants_access(self):
        """Sprawdza, czy poprawny PIN nadaje uprawnienia."""
        with self.client:
            response = self.client.post('/pin', data={'pin': '123456'}, follow_redirects=True)
            self.assertIn('Dostęp przyznany', response.get_data(as_text=True))
            self.assertTrue(session.get('is_pin_authenticated'))
            self.assertEqual(session.get('user_role'), 'reporter')

    def test_incorrect_pin_fails(self):
        """Sprawdza, czy błędny PIN nie daje dostępu."""
        with self.client:
            response = self.client.post('/pin', data={'pin': '000000'}, follow_redirects=True)
            self.assertIn('Nieprawidłowy kod PIN', response.get_data(as_text=True))
            self.assertFalse(session.get('is_pin_authenticated'))

if __name__ == '__main__':
    unittest.main()
