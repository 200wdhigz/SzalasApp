#!/usr/bin/env python3
"""
Skrypt migracyjny do dodania pól first_name i last_name do istniejących użytkowników.
Skrypt sprawdza użytkowników i ustawia domyślne wartości None dla nowych pól.
"""

import os
import sys

# Dodaj ścieżkę do katalogu nadrzędnego, aby móc importować moduły z src
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, app_dir)

# Załaduj zmienne środowiskowe NAJPIERW
from dotenv import load_dotenv
load_dotenv()

# Ustaw ścieżkę do service account (jeśli nie jest ustawiona) PRZED importem Firebase
# Musimy użyć ścieżki bezwzględnej, ponieważ .env ma ścieżkę względną
service_account_path = os.path.join(
    os.path.dirname(app_dir),
    'credentials',
    'service-account.json'
)

# Zawsze ustaw bezwzględną ścieżkę (nadpisz względną z .env)
if os.path.exists(service_account_path):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_path
    print(f"✅ Ustawiono GOOGLE_APPLICATION_CREDENTIALS: {service_account_path}")

# TERAZ zaimportuj Firebase
from firebase_admin import credentials, initialize_app, _apps
from google.cloud import firestore

# Sprawdź czy Firebase jest już zainicjalizowany
if not _apps:
    try:
        # Spróbuj użyć Application Default Credentials (teraz powinno zadziałać)
        cred = credentials.ApplicationDefault()
        initialize_app(cred, {'projectId': os.getenv('GOOGLE_PROJECT_ID')})
        print("✅ Firebase zainicjalizowany")
    except Exception as e:
        # Jeśli nie ma ADC, spróbuj użyć service account bezpośrednio
        if os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            initialize_app(cred, {'projectId': os.getenv('GOOGLE_PROJECT_ID')})
            print("✅ Firebase zainicjalizowany z Service Account")
        else:
            print(f"❌ Nie można zainicjalizować Firebase: {e}")
            print(f"   Sprawdź czy plik {service_account_path} istnieje")
            sys.exit(1)

# Teraz możemy zaimportować funkcję get_firestore_client
from src import get_firestore_client


def migrate_user_names():
    """
    Migruje istniejących użytkowników dodając pola first_name i last_name.
    """
    db = get_firestore_client()
    users_ref = db.collection('users')

    print("🔄 Rozpoczynam migrację użytkowników...")

    # Pobierz wszystkich użytkowników
    users = users_ref.stream()

    updated_count = 0
    skipped_count = 0

    for user_doc in users:
        user_data = user_doc.to_dict()
        user_id = user_doc.id
        email = user_data.get('email', 'N/A')

        # Sprawdź czy użytkownik już ma pola first_name i last_name
        if 'first_name' in user_data and 'last_name' in user_data:
            print(f"⏭️  Użytkownik {email} już ma pola first_name i last_name - pomijam")
            skipped_count += 1
            continue

        # Dodaj pola jeśli nie istnieją
        update_data = {}
        if 'first_name' not in user_data:
            update_data['first_name'] = None
        if 'last_name' not in user_data:
            update_data['last_name'] = None

        if update_data:
            update_data['updated_at'] = firestore.SERVER_TIMESTAMP
            users_ref.document(user_id).update(update_data)
            print(f"✅ Zaktualizowano użytkownika: {email}")
            updated_count += 1

    print("\n" + "="*60)
    print(f"📊 Podsumowanie migracji:")
    print(f"   Zaktualizowano: {updated_count} użytkowników")
    print(f"   Pominięto: {skipped_count} użytkowników")
    print("="*60)
    print("✨ Migracja zakończona!")


if __name__ == "__main__":
    try:
        migrate_user_names()
    except Exception as e:
        print(f"❌ Wystąpił błąd podczas migracji: {e}")
        sys.exit(1)

