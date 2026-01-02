#!/usr/bin/env python3
"""
Skrypt do przygotowania dokumentacji dla GitHub Wiki
Konwertuje pliki z docs/ do formatu Wiki i naprawia linki.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, Tuple

# Konfiguracja
SOURCE_DIR = Path('docs')  # Relatywne do wiki/
WIKI_DIR = Path('export')  # Relatywne do wiki/
REPO_URL = 'https://github.com/200wdhigz/SzalasApp'

# Mapowanie nazw plików docs → Wiki
FILE_MAPPING = {
    '00_INDEX.md': 'Home.md',
    'README.md': 'Documentation-Index.md',
    '01_QUICK_START.md': 'Quick-Start.md',
    '02_ARCHITECTURE.md': 'Architecture.md',
    '03_OAUTH_SETUP.md': 'OAuth-Setup.md',
    '04_ACCOUNT_MANAGEMENT.md': 'Account-Management.md',
    '05_USER_SYNC.md': 'User-Synchronization.md',
    '06_EQUIPMENT_MANAGEMENT.md': 'Equipment-Management.md',
    '07_MALFUNCTION_SYSTEM.md': 'Malfunction-System.md',
    '08_DATA_EXPORT.md': 'Data-Export.md',
    '09_ADMIN_PANEL.md': 'Admin-Panel.md',
    '10_SECURITY.md': 'Security.md',
    '11_BACKUP_RESTORE.md': 'Backup-and-Restore.md',
    '12_INSTALLATION.md': 'Installation.md',
    '13_DOCKER.md': 'Docker-Deployment.md',
    '14_MONITORING.md': 'Monitoring-and-Logs.md',
    '15_RECAPTCHA.md': 'ReCAPTCHA.md',
    '16_FIREBASE.md': 'Firebase-Configuration.md',
    '17_EMAIL_SMTP.md': 'Email-SMTP.md',
    '18_CHANGELOG.md': 'Changelog.md',
    '19_FAQ.md': 'FAQ.md',
    '20_TROUBLESHOOTING.md': 'Troubleshooting.md',
    '21_DEVELOPMENT.md': 'Development.md',
    '22_TESTING.md': 'Testing.md',
    '23_CONTRIBUTING.md': 'Contributing.md',
    '24_DEPENDENCIES.md': 'Dependencies-Guide.md',
    '25_FEATURE_SUMMARY.md': 'Feature-Summary.md',
    '26_DEPLOYMENT_PRODUCTION.md': 'Deployment-Production.md',
    'NPM_INDEX.md': 'NPM-Deployment-Index.md',
}


def convert_links_to_wiki(content: str, file_mapping: Dict[str, str]) -> str:
    """
    Konwertuje linki markdown do formatu GitHub Wiki.

    Przykład:
    [tekst](docs/01_QUICK_START.md) → [tekst](Quick-Start)
    [tekst](01_QUICK_START.md#sekcja) → [tekst](Quick-Start#sekcja)
    [tekst](../../FILE.md) → [tekst](https://github.com/.../blob/main/FILE.md)
    """
    # Utwórz mapę: nazwa pliku → nazwa wiki (bez .md)
    link_map = {}
    for source, wiki in file_mapping.items():
        wiki_name = wiki.replace('.md', '')
        link_map[source] = wiki_name
        link_map[f"docs/{source}"] = wiki_name
        link_map[f"../docs/{source}"] = wiki_name
        link_map[f"./{source}"] = wiki_name

    def replace_link(match):
        full_match = match.group(0)
        text = match.group(1)
        path = match.group(2)
        anchor = match.group(3) if match.lastindex >= 3 and match.group(3) else ""

        # Jeśli to link zewnętrzny (http/https), zostaw bez zmian
        if path.startswith(('http://', 'https://', '#')):
            return full_match

        # Usuń docs/ prefix jeśli istnieje
        clean_path = path.replace('docs/', '').replace('../docs/', '').replace('./', '')

        # Sprawdź czy jest w mapie (plik wiki)
        if clean_path in link_map:
            wiki_name = link_map[clean_path]
            return f"[{text}]({wiki_name}{anchor})"

        # Jeśli link zaczyna się od ../../ (plik w repo głównym, nie w wiki)
        if path.startswith('../../'):
            # Usuń ../../ i zamień na pełny link GitHub
            repo_path = path.replace('../../', '')
            github_link = f"{REPO_URL}/blob/main/{repo_path}"
            return f"[{text}]({github_link}{anchor})"

        # Jeśli nie znaleziono, zostaw bez zmian (może być to link do pliku zewnętrznego)
        return full_match

    # Pattern dla linków markdown: [text](path) lub [text](path#anchor)
    pattern = r'\[([^\]]+)\]\(([^)#]+)(#[^)]*)?\)'
    content = re.sub(pattern, replace_link, content)

    return content


def fix_special_characters(content: str) -> str:
    """Naprawia znaki specjalne które mogą powodować problemy w Wiki."""
    # GitHub Wiki nie lubi niektórych emoji w nagłówkach
    # Zostawiamy je w treści, ale usuwamy z nagłówków jeśli powodują problemy
    return content


def create_sidebar(wiki_dir: Path) -> None:
    """Tworzy pasek boczny _Sidebar.md."""
    sidebar_content = """## 📚 SzalasApp Wiki

### 🚀 Start
* [Strona Główna](Home)
* [Szybki Start](Quick-Start)
* [FAQ](FAQ)

### 📖 Podstawy
* [Architektura](Architecture)
* [OAuth Setup](OAuth-Setup)
* [Zarządzanie Kontami](Account-Management)
* [Synchronizacja Użytkowników](User-Synchronization)

### 🔧 Funkcje Systemu
* [Zarządzanie Sprzętem](Equipment-Management)
* [System Usterek](Malfunction-System)
* [Eksport Danych](Data-Export)

### 👨‍💼 Administracja
* [Panel Administratora](Admin-Panel)
* [Bezpieczeństwo](Security)
* [Backup i Restore](Backup-and-Restore)

### 🚀 Deployment
* [Instalacja](Installation)
* [Docker](Docker-Deployment)
* [Deployment Produkcyjny](Deployment-Production)
* [NPM Deployment](NPM-Deployment-Index) ⭐
* [Monitoring](Monitoring-and-Logs)

### 🔌 Integracje
* [Firebase](Firebase-Configuration)
* [reCAPTCHA](ReCAPTCHA)
* [Email SMTP](Email-SMTP)

### 💻 Dla Deweloperów
* [Development](Development)
* [Testing](Testing)
* [Contributing](Contributing)
* [Dependencies](Dependencies-Guide)

### 📝 Inne
* [Index Dokumentacji](Documentation-Index)
* [Changelog](Changelog)
* [Troubleshooting](Troubleshooting)
* [Feature Summary](Feature-Summary)

---

**v1.2.0** | [GitHub]({REPO_URL})
"""

    sidebar_path = wiki_dir / '_Sidebar.md'
    with open(sidebar_path, 'w', encoding='utf-8') as f:
        f.write(sidebar_content.replace('{REPO_URL}', REPO_URL))

    print("✅ Utworzono _Sidebar.md")


def create_footer(wiki_dir: Path) -> None:
    """Tworzy stopkę _Footer.md."""
    footer_content = f"""---
**SzalasApp v1.2.0** | System Zarządzania Sprzętem | [GitHub]({REPO_URL}) | [Zgłoś problem]({REPO_URL}/issues) | [Wiki Home](Home)
"""

    footer_path = wiki_dir / '_Footer.md'
    with open(footer_path, 'w', encoding='utf-8') as f:
        f.write(footer_content)

    print("✅ Utworzono _Footer.md")


def prepare_wiki_files() -> Tuple[int, int]:
    """
    Główna funkcja konwertująca pliki dokumentacji do GitHub Wiki.

    Returns:
        Tuple[int, int]: (liczba przetworzonych plików, liczba błędów)
    """
    print("=" * 60)
    print("Przygotowanie dokumentacji dla GitHub Wiki")
    print("=" * 60)
    print()

    # Utwórz folder docelowy
    if WIKI_DIR.exists():
        print(f"⚠️  Folder {WIKI_DIR} istnieje, czyszczę...")
        shutil.rmtree(WIKI_DIR)

    WIKI_DIR.mkdir(exist_ok=True)
    print(f"✅ Utworzono folder: {WIKI_DIR}")
    print()

    processed = 0
    errors = 0

    # Przetwórz każdy plik
    for source_file, wiki_file in FILE_MAPPING.items():
        source_path = SOURCE_DIR / source_file
        wiki_path = WIKI_DIR / wiki_file

        if not source_path.exists():
            print(f"⚠️  Pominięto: {source_file} (nie istnieje)")
            continue

        try:
            # Przeczytaj zawartość
            with open(source_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Konwertuj linki
            content = convert_links_to_wiki(content, FILE_MAPPING)

            # Napraw znaki specjalne
            content = fix_special_characters(content)

            # Zapisz
            with open(wiki_path, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"✅ {source_file:40} → {wiki_file}")
            processed += 1

        except Exception as e:
            print(f"❌ Błąd przy {source_file}: {str(e)}")
            errors += 1

    print()
    print("-" * 60)

    # Utwórz specjalne pliki Wiki
    create_sidebar(WIKI_DIR)
    create_footer(WIKI_DIR)

    print()
    print("=" * 60)
    print(f"Podsumowanie:")
    print(f"  ✅ Przetworzono: {processed} plików")
    print(f"  ❌ Błędów: {errors}")
    print(f"  📁 Lokalizacja: {WIKI_DIR.absolute()}")
    print("=" * 60)

    return processed, errors


def print_instructions():
    """Wyświetla instrukcje użycia."""
    print()
    print("=" * 60)
    print("Następne kroki:")
    print("=" * 60)
    print()
    print("1. Sklonuj wiki swojego repozytorium:")
    print(f"   git clone {REPO_URL}.wiki.git")
    print()
    print("2. Skopiuj wygenerowane pliki:")
    print("   # Windows (PowerShell):")
    print(f"   Copy-Item -Path wiki\\export\\* -Destination SzalasApp.wiki\\ -Force")
    print()
    print("   # Linux/Mac:")
    print(f"   cp wiki/export/* SzalasApp.wiki/")
    print()
    print("3. Commituj i wypchnij:")
    print("   cd SzalasApp.wiki")
    print("   git add .")
    print('   git commit -m "Update documentation"')
    print("   git push origin master")
    print()
    print("4. Zobacz wiki na:")
    print(f"   {REPO_URL}/wiki")
    print()
    print("   UWAGA: Uruchom ten skrypt z folderu wiki/:")
    print("   cd wiki")
    print("   python prepare_wiki.py")
    print()
    print("=" * 60)


if __name__ == '__main__':
    try:
        processed, errors = prepare_wiki_files()

        if errors == 0:
            print()
            print("🎉 Wszystkie pliki przygotowane pomyślnie!")
            print_instructions()
        else:
            print()
            print(f"⚠️  Zakończono z {errors} błędami")
            print("   Sprawdź logi powyżej i napraw problemy")

    except KeyboardInterrupt:
        print()
        print("⚠️  Przerwano przez użytkownika")
    except Exception as e:
        print()
        print(f"❌ Krytyczny błąd: {str(e)}")
        import traceback
        traceback.print_exc()


