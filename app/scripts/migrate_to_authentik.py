#!/usr/bin/env python3
"""
Skrypt do migracji użytkowników z Google/Microsoft OAuth na Authentik.
Przydatne gdy chcesz przenieść autoryzację z zewnętrznych dostawców na własną instancję Authentik.

Użycie:
    python migrate_to_authentik.py --dry-run  # Sprawdź co zostanie zmienione
    python migrate_to_authentik.py           # Wykonaj migrację
    python migrate_to_authentik.py --provider google  # Migruj tylko użytkowników Google
"""

import os
import sys
from pathlib import Path

# Dodaj katalog główny aplikacji do PYTHONPATH
app_root = Path(__file__).parent.parent
sys.path.insert(0, str(app_root))

import argparse
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe
load_dotenv(app_root / '.env')

from src import _init_firebase_admin, get_firestore_client
from src.db_users import get_all_users, update_user

def migrate_users_to_authentik(dry_run=True, provider='all'):
    """
    Migruje użytkowników z Google/Microsoft na Authentik.

    Args:
        dry_run: Jeśli True, tylko pokazuje co zostanie zmienione
        provider: 'google', 'microsoft' lub 'all'
    """
    _init_firebase_admin()

    print("=" * 80)
    print("Migracja użytkowników na Authentik OAuth")
    print("=" * 80)
    print(f"Tryb: {'DRY RUN (symulacja)' if dry_run else 'PRODUKCJA'}")
    print(f"Provider: {provider}")
    print("=" * 80)
    print()

    users = get_all_users()

    google_count = 0
    microsoft_count = 0
    authentik_count = 0
    skipped_count = 0

    for user in users:
        user_id = user['id']
        email = user.get('email', 'brak emaila')
        name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or email

        has_google = user.get('google_id') is not None
        has_microsoft = user.get('microsoft_id') is not None
        has_authentik = user.get('authentik_id') is not None

        if has_authentik:
            authentik_count += 1
            print(f"✓ {name} ({email}) - już ma Authentik")
            continue

        should_migrate = False
        migration_source = []

        if provider in ['all', 'google'] and has_google:
            should_migrate = True
            migration_source.append('Google')
            google_count += 1

        if provider in ['all', 'microsoft'] and has_microsoft:
            should_migrate = True
            migration_source.append('Microsoft')
            microsoft_count += 1

        if should_migrate:
            source_str = " i ".join(migration_source)
            print(f"→ {name} ({email}) - do migracji z {source_str}")
            print(f"   User ID: {user_id}")

            if not dry_run:
                # W rzeczywistości tutaj trzeba by:
                # 1. Utworzyć użytkownika w Authentik (jeśli nie istnieje)
                # 2. Pobrać authentik_id użytkownika (sub claim z Authentik)
                # 3. Zaktualizować rekord w Firestore

                # Placeholder - wymaga integracji z Authentik API lub ręcznej migracji
                print(f"   UWAGA: Musisz ręcznie utworzyć użytkownika w Authentik i ustawić authentik_id")
                print(f"   Po utworzeniu użytkownika w Authentik, wykonaj:")
                print(f"   update_user('{user_id}', authentik_id='<sub-value-from-authentik>')")
                print()
        else:
            if not (has_google or has_microsoft):
                skipped_count += 1
                print(f"  {name} ({email}) - brak OAuth (tylko hasło)")

    print()
    print("=" * 80)
    print("Podsumowanie:")
    print(f"  Użytkownicy z Google do migracji: {google_count}")
    print(f"  Użytkownicy z Microsoft do migracji: {microsoft_count}")
    print(f"  Użytkownicy już z Authentik: {authentik_count}")
    print(f"  Pominięto (tylko hasło): {skipped_count}")
    print(f"  Razem użytkowników: {len(users)}")
    print("=" * 80)

    if dry_run:
        print()
        print("To był DRY RUN. Aby wykonać migrację, uruchom bez --dry-run")
        print()
        print("=" * 80)
        print("INSTRUKCJA MIGRACJI:")
        print("=" * 80)
        print()
        print("1. Skonfiguruj Authentik OAuth w aplikacji:")
        print("   - Utwórz Provider (OAuth2/OpenID)")
        print("   - Utwórz Application i podłącz Provider")
        print("   - Skopiuj Client ID i Client Secret do .env")
        print()
        print("2. Dla każdego użytkownika w Authentik:")
        print("   - Utwórz użytkownika z tym samym emailem")
        print("   - Pobierz 'sub' claim użytkownika (UUID)")
        print("   - Zaktualizuj rekord w Firestore:")
        print()
        print("   from src.db_users import update_user")
        print("   update_user('firebase-uid', authentik_id='authentik-sub-uuid')")
        print()
        print("3. Opcjonalnie usuń stare powiązania:")
        print("   update_user('firebase-uid', google_id=None)")
        print("   update_user('firebase-uid', microsoft_id=None)")
        print()
        print("4. Przetestuj logowanie przez Authentik")
        print()
        print("=" * 80)
        print()
        print("TIP: Możesz użyć Authentik API do automatyzacji tworzenia użytkowników")
        print("     https://docs.goauthentik.io/developer-docs/api/")


def migrate_single_user(user_id: str, authentik_id: str, remove_old_oauth: bool = False):
    """
    Migruje pojedynczego użytkownika na Authentik.

    Args:
        user_id: Firebase UID użytkownika
        authentik_id: Sub claim z Authentik
        remove_old_oauth: Czy usunąć stare powiązania Google/Microsoft
    """
    _init_firebase_admin()

    from src.db_users import get_user_by_uid, update_user

    user = get_user_by_uid(user_id)
    if not user:
        print(f"❌ Nie znaleziono użytkownika: {user_id}")
        return

    email = user.get('email', 'brak emaila')
    name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or email

    print(f"Migracja użytkownika: {name} ({email})")
    print(f"Firebase UID: {user_id}")
    print(f"Authentik ID: {authentik_id}")

    update_data = {'authentik_id': authentik_id}

    if remove_old_oauth:
        print("Usuwanie starych powiązań OAuth...")
        update_data['google_id'] = None
        update_data['microsoft_id'] = None

    update_user(user_id, **update_data)
    print("✅ Migracja zakończona pomyślnie!")


def main():
    parser = argparse.ArgumentParser(description='Migracja użytkowników na Authentik OAuth')
    parser.add_argument('--dry-run', action='store_true',
                       help='Tylko pokaż co zostanie zmienione')
    parser.add_argument('--provider', choices=['google', 'microsoft', 'all'], default='all',
                       help='Który provider migrować (domyślnie: all)')
    parser.add_argument('--user-id', type=str,
                       help='Migruj pojedynczego użytkownika (wymaga --authentik-id)')
    parser.add_argument('--authentik-id', type=str,
                       help='Authentik sub ID dla pojedynczego użytkownika')
    parser.add_argument('--remove-old-oauth', action='store_true',
                       help='Usuń stare powiązania Google/Microsoft po migracji')

    args = parser.parse_args()

    if args.user_id and args.authentik_id:
        migrate_single_user(args.user_id, args.authentik_id, args.remove_old_oauth)
    elif args.user_id or args.authentik_id:
        print("❌ Błąd: Musisz podać zarówno --user-id jak i --authentik-id")
        sys.exit(1)
    else:
        migrate_users_to_authentik(dry_run=args.dry_run, provider=args.provider)


if __name__ == '__main__':
    main()

