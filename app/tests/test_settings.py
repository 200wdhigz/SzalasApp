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

class SettingsTemplateTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_settings_page_renders_with_pin_last_rotate(self):
        """Sprawdza, czy strona ustawień renderuje się poprawnie, gdy ustawiony jest pin_last_rotate."""
        from datetime import datetime
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 'test_admin'
            sess['user_role'] = 'admin'
            sess['is_admin'] = True

        # Symulujemy dane w configu. Ponieważ get_config pobiera z Firestore, 
        # a my nie chcemy modyfikować prawdziwej bazy w testach (chyba że mamy emulator),
        # spróbujemy użyć mocka lub po prostu sprawdzimy czy błąd hasattr występuje.
        # W tym projekcie testy wydają się używać prawdziwego Firestore (patrząc na test_pin_access.py).
        
        # Ustawiamy pin_last_rotate jako datetime
        with self.app.app_context():
            from src.db_firestore import _warsaw_now
            update_config(pin_last_rotate=_warsaw_now())

        response = self.client.get('/admin/settings')
        self.assertEqual(response.status_code, 200)
        # Jeśli hasattr jest niezdefiniowany, to rzuci 500 i test padnie (lub zwróci 500)
        
    def test_settings_page_renders_with_string_pin_last_rotate(self):
        """Sprawdza, czy strona ustawień renderuje się poprawnie, gdy pin_last_rotate jest stringiem."""
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
