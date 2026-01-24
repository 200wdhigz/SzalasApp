import unittest
import sys
import os

# Dodaj folder 'app' do ścieżki, aby importy działały
sys.path.append(os.path.join(os.getcwd(), 'app'))

# Popraw ścieżkę do credentials dla testu, jeżeli uruchamiamy z roota
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"C:\Users\uzyt\PycharmProjects\SzalasApp\credentials\service-account.json"

from src import create_app
from src.db_firestore import (
    update_config,
    add_item,
    delete_item,
    get_items_by_filter,
    COLLECTION_SPRZET,
    COLLECTION_USTERKI,
    COLLECTION_WYPOZYCZENIA,
)

class RestrictedPinAccessTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        
        self._loan_id = None

        # Ustawienie testowego PINu
        with self.app.app_context():
            update_config(view_pin='123456', pin_auto_rotate=False)
            # Dodaj testowy sprzęt
            self.sprzet_id = "TEST_RESTRICT"
            add_item(COLLECTION_SPRZET, {
                'id': self.sprzet_id,
                'nazwa': 'Testowy Sprzęt',
                'typ': 'Test',
                'category': 'przedmiot',
                'informacje': 'Tajne dane techniczne'
            })
            # Dodaj testową usterkę
            self.usterka_id = "TEST_USTERKA"
            add_item(COLLECTION_USTERKI, {
                'id': self.usterka_id,
                'sprzet_id': self.sprzet_id,
                'opis': 'Zepsute coś tam',
                'status': 'oczekuje'
            })
            # Dodaj aktywne wypożyczenie z danymi kontaktowymi
            self._loan_id = add_item(COLLECTION_WYPOZYCZENIA, {
                 'item_id': self.sprzet_id,
                 'przez_kogo': 'Jan Kowalski',
                 'kontakt': '123-456-789',
                 'status': 'active'
             })

    def tearDown(self):
        # Usuwaj dane testowe niezależnie od wyniku testu.
        with self.app.app_context():
            # usuń wypożyczenie (po id jeśli znamy; jeśli nie, znajdź po item_id)
            try:
                if self._loan_id:
                    delete_item(COLLECTION_WYPOZYCZENIA, self._loan_id)
                else:
                    loans = get_items_by_filter(COLLECTION_WYPOZYCZENIA, 'item_id', '==', getattr(self, 'sprzet_id', ''))
                    for l in loans or []:
                        if l.get('status') == 'active':
                            delete_item(COLLECTION_WYPOZYCZENIA, l['id'])
            except Exception:
                pass

            # usuń usterkę
            try:
                if getattr(self, 'usterka_id', None):
                    delete_item(COLLECTION_USTERKI, self.usterka_id)
            except Exception:
                pass

            # usuń sprzęt
            try:
                if getattr(self, 'sprzet_id', None):
                    delete_item(COLLECTION_SPRZET, self.sprzet_id)
            except Exception:
                pass

    def _login_via_pin(self):
        return self.client.post('/pin', data={'pin': '123456'}, follow_redirects=True)

    def test_pin_user_cannot_access_lists(self):
        """PIN user should NOT access lists of equipment, summary, and defects."""
        self._login_via_pin()
        
        # /sprzety
        response = self.client.get('/sprzety')
        # Currently it returns 200, but we want it to redirect or deny
        self.assertNotEqual(response.status_code, 200, "PIN user should not access /sprzety")
        
        # /sprzet/zestawienie
        response = self.client.get('/sprzet/zestawienie')
        self.assertNotEqual(response.status_code, 200, "PIN user should not access /sprzet/zestawienie")
        
        # /usterki
        response = self.client.get('/usterki')
        self.assertNotEqual(response.status_code, 200, "PIN user should not access /usterki")

    def test_pin_user_can_access_cards(self):
        """PIN user SHOULD access equipment and defect cards."""
        self._login_via_pin()
        
        # /sprzet/<id>
        response = self.client.get(f'/sprzet/{self.sprzet_id}')
        self.assertEqual(response.status_code, 200)
        
        # /usterka/<id>
        response = self.client.get(f'/usterka/{self.usterka_id}')
        self.assertEqual(response.status_code, 200)

    def test_pin_user_restricted_content_on_sprzet_card(self):
        """PIN user should see technical data, photos, defects, but NO loan history, NO contact info, NO add defect form."""
        self._login_via_pin()
        
        response = self.client.get(f'/sprzet/{self.sprzet_id}')
        html = response.get_data(as_text=True)
        
        # Technical data
        self.assertIn('Tajne dane techniczne', html)
        
        # Defects
        self.assertIn('Zepsute coś tam', html)
        
        # Current loan status (is it loaned)
        self.assertIn('Ten przedmiot jest obecnie wypożyczony', html)
        
        # NO Contact info
        self.assertNotIn('123-456-789', html)
        
        # NO Loan History / Logs
        self.assertNotIn('Historia Aktywności', html)
        self.assertNotIn('Historia wypożyczeń', html) # Check exact strings in template later
        
        # NO Add Defect Form
        self.assertNotIn('Zgłoś Nową Usterkę', html)

    def test_pin_user_cannot_post_defect(self):
        """PIN user should not be able to POST a new defect."""
        self._login_via_pin()
        
        response = self.client.post(f'/sprzet/{self.sprzet_id}', data={
            'opis_usterki': 'Próba zgłoszenia przez PIN'
        }, follow_redirects=True)
        
        # Should either redirect to login/pin or show error
        self.assertNotIn('Usterka dla TEST_RESTRICT została zgłoszona!', response.get_data(as_text=True))

if __name__ == '__main__':
    unittest.main()
