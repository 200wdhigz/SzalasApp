import unittest
import sys
import os

# Dodaj folder 'app' do ścieżki, aby importy działały
sys.path.append(os.path.join(os.getcwd(), 'app'))

# Popraw ścieżkę do credentials dla testu, jeśli uruchamiamy z roota
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(os.getcwd(), 'credentials', 'service-account.json')

from src import create_app
from src.db_firestore import update_config

class PinRedirectSecurityTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        
        # Ustawienie testowego PINu
        with self.app.app_context():
            update_config(view_pin='123456', pin_auto_rotate=False)

    def test_blocks_external_redirect(self):
        """Sprawdza, czy zewnętrzne URL są blokowane w przekierowaniu."""
        with self.client:
            response = self.client.post('/pin?next=http://evil.com', data={'pin': '123456'})
            self.assertEqual(response.status_code, 302)
            # Powinno przekierować do bezpiecznej strony domyślnej, nie do evil.com
            self.assertNotIn('evil.com', response.location)
            self.assertIn('/sprzet', response.location)

    def test_blocks_absolute_url_with_scheme(self):
        """Sprawdza, czy URL ze schematem są blokowane."""
        with self.client:
            response = self.client.post('/pin?next=https://malicious.com/steal', data={'pin': '123456'})
            self.assertEqual(response.status_code, 302)
            self.assertNotIn('malicious.com', response.location)
            self.assertIn('/sprzet', response.location)

    def test_allows_relative_redirect(self):
        """Sprawdza, czy względne URL są dozwolone."""
        with self.client:
            response = self.client.post('/pin?next=/sprzet/test_id', data={'pin': '123456'})
            self.assertEqual(response.status_code, 302)
            self.assertIn('/sprzet/test_id', response.location)

    def test_blocks_backslash_bypass(self):
        """Sprawdza, czy próba obejścia z backslash jest blokowana."""
        with self.client:
            response = self.client.post('/pin?next=\\evil.com', data={'pin': '123456'})
            self.assertEqual(response.status_code, 302)
            self.assertNotIn('evil.com', response.location)

    def test_blocks_backslash_slash_bypass(self):
        """Sprawdza, czy próba obejścia z /\\ jest blokowana."""
        with self.client:
            response = self.client.post('/pin?next=/\\evil.com', data={'pin': '123456'})
            self.assertEqual(response.status_code, 302)
            self.assertNotIn('evil.com', response.location)
            self.assertIn('/sprzet', response.location)

    def test_blocks_protocol_relative_url(self):
        """Sprawdza, czy URL względne do protokołu są blokowane."""
        with self.client:
            response = self.client.post('/pin?next=//evil.com', data={'pin': '123456'})
            self.assertEqual(response.status_code, 302)
            self.assertNotIn('evil.com', response.location)
            self.assertIn('/sprzet', response.location)

    def test_default_redirect_when_no_next(self):
        """Sprawdza domyślne przekierowanie gdy brak parametru next."""
        with self.client:
            response = self.client.post('/pin', data={'pin': '123456'})
            self.assertEqual(response.status_code, 302)
            self.assertIn('/sprzet', response.location)

if __name__ == '__main__':
    unittest.main()
