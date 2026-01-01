import pandas as pd
import os
from dotenv import load_dotenv
from google.cloud import firestore
from src.db_firestore import add_item, COLLECTION_SPRZET

load_dotenv()

DATA_DIR = 'data'
IGNORE_FILES = ['baza danych - Arkusz5.csv', 'baza danych - Arkusz7.csv', 'baza danych - Arkusz4.csv']

def import_csv_to_firestore(file_path):
    """Importuje dane z CSV do Firestore."""
    try:
        df = pd.read_csv(file_path, on_bad_lines='skip').fillna('')
        mapping = {
            'Typ': 'typ', 'ID': 'id', 'Zakup': 'zakup', 'Przejęty': 'przejecie',
            'Znak szczególny': 'znak_szczegolny', 'Zapałki': 'zapalki',
            'Kolor dachu': 'kolor_dachu', 'Kolor boków': 'kolor_bokow',
            'ZMIANA STANU (WRACA DO WARSZAWY)': 'czyWraca',
            'Wodoszczelność': 'wodoszczelnosc', 'Stan ogólny': 'stan_ogolny',
            'Uwagi konserwacyjne': 'uwagi', 'Magazyn': 'lokalizacja',
            'Przeznaczenie': 'przeznaczenie', 'Historia': 'historia',
            'Fotografie namiotów': 'zdjecie_glowne_url'
        }
        df = df.rename(columns=mapping)
        cols = list(mapping.values())
        df = df[[c for c in cols if c in df.columns]]
        df.columns = [c.lower() for c in df.columns]
        df = df[df['id'].str.match(r'^[A-Z]{2}\d{2,}$', na=False)]

        db = firestore.Client(project=os.getenv('GCP_PROJECT_ID'))
        batch = db.batch()
        count = 0

        for _, row in df.iterrows():
            sprzet_id = row['id']
            data = row.to_dict()
            del data['id']
            batch.set(db.collection(COLLECTION_SPRZET).document(sprzet_id), data)
            count += 1
            if count % 500 == 0:
                batch.commit()
                batch = db.batch()
        batch.commit()
        print(f"✅ Zaimportowano {count} rekordów z {os.path.basename(file_path)}.")
    except Exception as e:
        print(f"❌ Błąd w {os.path.basename(file_path)}: {e}")

if __name__ == '__main__':
    files = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) 
             if f.endswith('.csv') and f not in IGNORE_FILES]
    for f in files:
        import_csv_to_firestore(f)
