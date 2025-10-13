# set_admin_claim.py (Nowy plik do ręcznego uruchamiania)

import os
import sys
# Upewnienie się, że skrypty mogą się zaimportować
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from firebase_admin import auth
from app import create_app # Zakładając, że app.py ma create_app()

# ⚠️ ZMIEŃ TEN UID NA RZECZYWISTY UID UŻYTKOWNIKA DOCELOWEGO ⚠️
TARGET_UID = "kCoy3SWwm6O2fgRUXgKUOhCimpI3"

def set_custom_admin_claim(uid):
    """Nadaje użytkownikowi Custom Claim 'admin: True' za pomocą Firebase Admin SDK."""
    try:
        # KLUCZOWA FUNKCJA: ustawia claim, który będzie widoczny w tokenie ID
        auth.set_custom_user_claims(uid, {'admin': True})
        print(f"\n✅ Sukces: Użytkownik o UID: {uid} otrzymał uprawnienia administratora.")
        print("WAŻNE: Użytkownik musi WYLOWOWAĆ SIĘ i ZALOGOWAĆ PONOWNIE, aby token został odświeżony!")
    except Exception as e:
        print(f"\n❌ BŁĄD: {e}")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        if TARGET_UID == "WklejTutajUIDUzytkownika":
             print("!!! Proszę edytować plik set_admin_claim.py i podać prawidłowy TARGET_UID !!!")
        else:
             set_custom_admin_claim(TARGET_UID)
