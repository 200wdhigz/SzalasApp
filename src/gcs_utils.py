import os
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()

FIREBASE_STORAGE_BUCKET = os.getenv('FIREBASE_STORAGE_BUCKET_NAME')


def get_gcs_client():
    """Zwraca instancję klienta Google Cloud Storage z ID projektu."""
    # Używamy GCP_PROJECT_ID, aby uniknąć błędu OSError
    return storage.Client(project=os.getenv('GCP_PROJECT_ID'))


def list_sprzet_photos(sprzet_id: str) -> list:
    """
    Pobiera listę URL-i wszystkich zdjęć dla danego ID sprzętu z GCS.
    Zdjęcia są w folderze: sprzet/{sprzet_id}/
    """
    if not FIREBASE_STORAGE_BUCKET:
        print("Błąd: FIREBASE_STORAGE_BUCKET_NAME nie ustawiony.")
        return []

    client = get_gcs_client()
    bucket = client.bucket(FIREBASE_STORAGE_BUCKET)

    # Prefix to folder w GCS
    prefix = f"sprzet/{sprzet_id.upper()}/"

    # Lista wszystkich obiektów w tym folderze
    blobs = bucket.list_blobs(prefix=prefix)

    photo_urls = []

    for blob in blobs:
        # Ignoruj foldery (obiekty kończące się na /)
        if not blob.name.endswith('/'):
            # ❗ KLUCZOWA ZMIANA: Używamy formatu storage.googleapis.com
            url = f"https://storage.googleapis.com/{FIREBASE_STORAGE_BUCKET}/{blob.name}"
            photo_urls.append(url)

    photo_urls.sort()

    return photo_urls
