import os
import re
from dotenv import load_dotenv
from google.cloud import firestore
from src.gcs_utils import upload_blob_to_gcs, GCS_BUCKET_NAME
from src.db_firestore import COLLECTION_SPRZET

load_dotenv()

PHOTOS_DIR = 'photos'

def upload_and_update():
    """Wgrywa zdjęcia i aktualizuje Firestore."""
    if not os.path.exists(PHOTOS_DIR) or not GCS_BUCKET_NAME:
        print("❌ Brak katalogu zdjęć lub konfiguracji GCS.")
        return

    db = firestore.Client(project=os.getenv('GCP_PROJECT_ID'))
    count = 0

    for sprzet_id in os.listdir(PHOTOS_DIR):
        path = os.path.join(PHOTOS_DIR, sprzet_id)
        if not os.path.isdir(path) or not re.match(r'^[A-Z]{2}\d{2,}$', sprzet_id):
            continue

        photos = sorted([f for f in os.listdir(path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        urls = []
        for i, photo in enumerate(photos):
            ext = os.path.splitext(photo)[1].lower()
            blob_path = f"sprzet/{sprzet_id.upper()}/{sprzet_id.upper()}_foto{i:02d}{ext}"
            try:
                with open(os.path.join(path, photo), 'rb') as f_obj:
                    url = upload_blob_to_gcs(blob_path, f_obj, f"image/{ext[1:]}")
                urls.append(url)
            except Exception as e:
                print(f"❌ Błąd {photo}: {e}")

        if urls:
            db.collection(COLLECTION_SPRZET).document(sprzet_id.upper()).update({
                'zdjecie_glowne_url': urls[0],
                'zdjecia_lista_url': urls
            })
            print(f"✅ {sprzet_id} zaktualizowany.")
            count += 1
    print(f"--- Zakończono. Zaktualizowano {count} elementów. ---")

if __name__ == '__main__':
    upload_and_update()
