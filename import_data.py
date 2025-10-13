import pandas as pd
import os
from dotenv import load_dotenv
from google.cloud import firestore
import re

# Upewnij się, że zmienne środowiskowe są załadowane
load_dotenv()

# --------------------------
# KONFIGURACJA
# --------------------------
DATA_DIR = 'data'
COLLECTION_SPRZET = 'sprzet'
# Lista nazw plików, które chcemy zignorować (np. pliki pomocnicze, które nie są głównymi bazami sprzętu)
IGNORE_FILES = ['baza danych - Arkusz5.csv', 'baza danych - Arkusz7.csv', 'baza danych - Arkusz4.csv']


def get_firestore_client():
    """Zwraca instancję klienta Firestore."""
    return firestore.Client(project=os.getenv('GCP_PROJECT_ID'))


def get_csv_files(data_dir):
    """Skanuje katalog i zwraca listę plików CSV, ignorując pliki na liście IGNORE_FILES."""
    csv_files = []
    for filename in os.listdir(data_dir):
        if filename.endswith('.csv') and filename not in IGNORE_FILES:
            csv_files.append(os.path.join(data_dir, filename))
    return csv_files


def import_csv_to_firestore(file_path):
    """
    Czyta plik CSV, przetwarza kolumny i importuje dane do Firestore.
    """
    try:
        db = get_firestore_client()

        # Próbujemy odczytać, ignorując linie z błędami i wypełniając puste pola
        df = pd.read_csv(file_path, on_bad_lines='skip').fillna('')

        # UJEDNOLICENIE NAZW KOLUMN
        # Mapowanie nagłówków z pliku CSV na docelowe klucze Firestore
        df = df.rename(columns={
            'Typ': 'typ',
            'ID': 'id',
            'Zakup': 'zakup',
            'Przejęty': 'przejecie',
            'Znak szczególny': 'znak_szczegolny',
            'Zapałki': 'zapalki',
            'Kolor dachu': 'kolor_dachu',
            'Kolor boków': 'kolor_bokow',
            'ZMIANA STANU (WRACA DO WARSZAWY)': 'czyWraca',
            'Wodoszczelność': 'wodoszczelnosc',
            'Stan ogólny': 'stan_ogolny',  # Używamy małej litery 'ó' dla spójności z polskim
            'Uwagi konserwacyjne': 'uwagi',
            'Magazyn': 'lokalizacja',
            'Przeznaczenie': 'przeznaczenie',
            'Historia': 'historia',
            'Fotografie namiotów': 'zdjecie_glowne_url',
        })

        # Sprawdzenie, czy kolumna 'stan_ogolny' nie jest przypadkiem 'Stan ogólny' z dużej litery
        if 'Stan ogólny' in df.columns and 'stan_ogolny' not in df.columns:
            df = df.rename(columns={'Stan ogólny': 'stan_ogolny'})

        # FILTROWANIE KOLUMN I WIERSZY
        kolumny_docelowe = [
            'id', 'typ', 'zakup', 'przejecie', 'znak_szczegolny', 'zapalki',
            'kolor_dachu', 'kolor_bokow', 'czyWraca', 'wodoszczelnosc',
            'stan_ogolny', 'uwagi', 'lokalizacja', 'przeznaczenie',
            'historia', 'zdjecie_glowne_url'
        ]

        # Filtrowanie DF do tylko tych kolumn, które chcemy zapisać
        # Używamy .columns.intersection, aby brać tylko te, które istnieją w pliku
        df = df[[col for col in kolumny_docelowe if col in df.columns]]

        # Ujednolicenie nazw kolumn w DF (usunięcie zbędnych spacji, małe litery)
        df.columns = [col.lower() for col in df.columns]

        # Usuń wiersze, które nie mają poprawnego ID (typowy format: 2 litery i co najmniej 2 cyfry)
        df = df[df['id'].str.match(r'^[A-Z]{2}\d{2,}$', na=False)]

        # ZAPIS DO FIRESTORE
        db = get_firestore_client()
        batch = db.batch()
        count = 0

        for index, row in df.iterrows():
            if not row['id']: continue

            sprzet_id = row['id']
            data = row.to_dict()
            del data['id']

            # Wstawienie dokumentu z ID jako nazwą dokumentu Firestore
            doc_ref = db.collection(COLLECTION_SPRZET).document(sprzet_id)
            batch.set(doc_ref, data)
            count += 1

            if count % 500 == 0:
                batch.commit()
                batch = db.batch()

        batch.commit()

        print(f"✅ Pomyślnie zaimportowano/zaktualizowano {count} rekordów z pliku {os.path.basename(file_path)}.")

    except Exception as e:
        print(f"❌ Wystąpił błąd podczas importowania pliku {os.path.basename(file_path)}: {e}")
        print("Upewnij się, że nagłówki kolumn są poprawne i zgodne z oczekiwanymi.")


def import_all_data():
    """Importuje wszystkie odpowiednie pliki CSV z katalogu DATA_DIR."""
    files_to_import = get_csv_files(DATA_DIR)

    if not files_to_import:
        print(f"⚠️ Nie znaleziono żadnych plików CSV w katalogu {DATA_DIR} (po odfiltrowaniu ignorowanych).")
        return

    for file_path in files_to_import:
        import_csv_to_firestore(file_path)


if __name__ == '__main__':
    print("--- ROZPOCZYNAM DYNAMICZNY IMPORT DANYCH DO FIRESTORE ---")
    import_all_data()
    print("--- IMPORT ZAKOŃCZONY ---")
