import sqlite3
import pandas as pd
import os

# Lista plików CSV do zaimportowania
# ZMIENIASZ TUTAJ: Wymień wszystkie swoje pliki CSV z namiotami, aby załadować całą bazę
CSV_FILES = [
    "baza danych - DD, MD i MAZ.csv",
    # "baza danych - NS i podpinki.csv", # odkomentuj, gdy chcesz je załadować
    # "baza danych - namioty turystyczne.csv",
    # "baza danych - zadaszenia i plandeki.csv",
    # ... i pozostałe
]

DB_NAME = os.getenv('DB_NAME')


def create_db_and_import():
    """Tworzy bazę danych i importuje do niej dane z plików CSV."""

    print(f"Łączenie z bazą danych: {DB_NAME}")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tabela 1: SPRZĘT (Główny Katalog)
    # Używamy ustandaryzowanych nazw kolumn, aby były łatwiejsze w kodzie.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sprzet (
            id TEXT PRIMARY KEY,
            typ TEXT,
            opis_qr TEXT,
            zakup TEXT,
            przejety TEXT,
            znak_szczegolny TEXT,
            zapalki TEXT,
            kolor TEXT,
            link_do_wiersza TEXT,
            stan TEXT,
            stan_ogolny TEXT,
            uwagi_konserwacyjne TEXT,
            miejsce_przechowywania TEXT,
            przeznaczenie TEXT,
            opis_ogolny TEXT
        )
    ''')
    print("Tabela 'sprzet' utworzona/zweryfikowana.")

    # Tabela 2: USTERKI (Zgłaszanie przez użytkowników)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usterki (
            usterka_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sprzet_id TEXT,
            data_zgloszenia TEXT DEFAULT CURRENT_TIMESTAMP,
            opis_usterki TEXT NOT NULL,
            zgloszono_przez TEXT,
            status TEXT DEFAULT 'NOWA',
            FOREIGN KEY (sprzet_id) REFERENCES sprzet(id)
        )
    ''')
    print("Tabela 'usterki' utworzona/zweryfikowana.")

    # Czyszczenie i Import Danych z CSV
    print("Rozpoczynanie importu danych...")
    for file_path in CSV_FILES:
        if not os.path.exists(file_path):
            print(f"Ostrzeżenie: Plik '{file_path}' nie został znaleziony. Pomijam.")
            continue

        print(f"Przetwarzanie pliku: {file_path}")

        # Wczytanie pliku CSV, ignorując puste wiersze i upewniając się, że separator to przecinek
        df = pd.read_csv(file_path, sep=',', skipinitialspace=True).dropna(how='all')

        # Mapowanie kolumn z CSV na nazwy kolumn w bazie danych
        # To jest kluczowy krok! Musisz dopasować nazwy w lewej kolumnie do nagłówków w Twoim CSV.
        column_mapping = {
            'ID': 'id',
            'Kolumna1': 'typ',  # Z Twojego CSV (np. 'duża dycha', 'mała dycha')
            'opis który pokazuje się po zeskanowaniu kodu QR ( NIE EDYTOWAĆ)': 'opis_qr',
            'Zakup': 'zakup',
            'Przejęty': 'przejety',
            'Znak szczególny': 'znak_szczegolny',
            'Zapałki': 'zapalki',
            'Kolor': 'kolor',
            'Link do wiersza': 'link_do_wiersza',
            'Stan': 'stan',
            'Stan ogólny': 'stan_ogolny',
            'Uwagi konserwacyjne': 'uwagi_konserwacyjne',
            'obecne miejsce przechowywania': 'miejsce_przechowywania',
            'przeznaczenie': 'przeznaczenie',
            'Opis (co o nim wiemy)': 'opis_ogolny'
        }

        # Filtrujemy tylko kolumny, które są obecne w DataFrame
        df_filtered = df[[col for col in column_mapping.keys() if col in df.columns]]
        df_filtered.rename(columns=column_mapping, inplace=True)

        # Usuń wiersze, gdzie brakuje kluczowego 'id' i upewnij się, że ID jest stringiem
        df_filtered = df_filtered.dropna(subset=['id'])
        df_filtered['id'] = df_filtered['id'].astype(str).str.strip()

        # Wstawienie danych do tabeli 'sprzet'
        # 'replace' pozwala na aktualizację danych, jeśli rekord o danym ID już istnieje (np. z innego pliku CSV)
        df_filtered.to_sql('sprzet', conn, if_exists='append', index=False)
        print(f"Zaimportowano {len(df_filtered)} rekordów z pliku: {file_path}")

    conn.commit()
    conn.close()
    print("Import zakończony! Baza danych gotowa.")


if __name__ == '__main__':
    create_db_and_import()
