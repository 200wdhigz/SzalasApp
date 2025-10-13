import os
from google.cloud import storage
from google.cloud import firestore
from dotenv import load_dotenv
import re

load_dotenv()

# --- KONFIGURACJA ---
PHOTOS_DIR = 'photos'
COLLECTION_SPRZET = 'sprzet'
FIREBASE_STORAGE_BUCKET = os.getenv('FIREBASE_STORAGE_BUCKET_NAME')


# --- KONFIGURACJA ---


def get_gcs_client():
    """Zwraca instancję klienta Google Cloud Storage."""
    return storage.Client(project=os.getenv('GCP_PROJECT_ID'))


def get_firestore_client():
    """Zwraca instancję klienta Firestore."""
    return firestore.Client(project=os.getenv('GCP_PROJECT_ID'))


def upload_and_update_firestore():
    """
    Skanuje katalog zdjęć, przesyła je do GCS z ujednoliconą nazwą
    i aktualizuje Firestore o URL do głównego zdjęcia (foto00).
    """
    if not os.path.exists(PHOTOS_DIR):
        print(f"❌ Katalog '{PHOTOS_DIR}' nie istnieje. Przerwanie.")
        return

    if not FIREBASE_STORAGE_BUCKET:
        print("❌ Brak zmiennej środowiskowej 'FIREBASE_STORAGE_BUCKET_NAME'. Przerwanie.")
        return

    gcs_client = get_gcs_client()
    db = get_firestore_client()
    bucket = gcs_client.bucket(FIREBASE_STORAGE_BUCKET)

    print(f"--- ROZPOCZYNAM PRZESYŁANIE ZDJĘĆ DO BUCKETA: {FIREBASE_STORAGE_BUCKET} ---")

    uploaded_count = 0

    for sprzet_id in os.listdir(PHOTOS_DIR):
        sprzet_folder_path = os.path.join(PHOTOS_DIR, sprzet_id)

        # 1. WERYFIKACJA FOLDERU
        if not os.path.isdir(sprzet_folder_path) or not re.match(r'^[A-Z]{2}\d{2,}$', sprzet_id):
            continue

        photos = [f for f in os.listdir(sprzet_folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        if not photos:
            print(f"⚠️ Pusty folder dla ID: {sprzet_id}")
            continue

        # Sortowanie, aby numeracja była spójna
        photos.sort()

        # Zbierz listę URL-i dla wszystkich zdjęć (dla przyszłej galerii)
        photo_urls = []
        main_photo_url = None

        # 2. ITERACJA I ZMIANA NAZW
        for index, original_name in enumerate(photos):
            local_file_path = os.path.join(sprzet_folder_path, original_name)

            # Nowa nazwa: ID_fotoXX.ext
            extension = os.path.splitext(original_name)[1].lower()
            new_name = f"{sprzet_id.upper()}_foto{index:02d}{extension}"  # np. DD01_foto00.jpg

            # Ścieżka docelowa w Storage: sprzet/DD01/DD01_foto00.jpg
            blob_path = f"sprzet/{sprzet_id.upper()}/{new_name}"
            blob = bucket.blob(blob_path)

            try:
                # Wgrywamy plik
                blob.upload_from_filename(local_file_path)

                # Generowanie URL dostępu publicznego
                # Wymaga, by reguły Storage były ustawione na zezwolenie na publiczny odczyt!
                image_url = f"https://firebasestorage.googleapis.com/v0/b/{FIREBASE_STORAGE_BUCKET}/o/{blob_path.replace('/', '%2F')}?alt=media"

                photo_urls.append(image_url)

                # Ustawiamy pierwsze zdjęcie jako główne
                if index == 0:
                    main_photo_url = image_url

                print(f"   -> Zapisano jako: {new_name}")

            except Exception as e:
                print(f"❌ Błąd podczas przesyłania pliku {original_name} dla ID {sprzet_id}: {e}")

        # 3. AKTUALIZACJA FIRESTORE (tylko główne zdjęcie i lista wszystkich)
        if main_photo_url:
            try:
                doc_ref = db.collection(COLLECTION_SPRZET).document(sprzet_id.upper())
                doc_ref.update({
                    'zdjecie_glowne_url': main_photo_url,
                    'zdjecia_lista_url': photo_urls  # Dodajemy listę URL-i dla przyszłej galerii
                })
                print(f"✅ Zaktualizowano Firestore: {sprzet_id} (Główne zdjęcie: {os.path.basename(main_photo_url)})")
                uploaded_count += 1
            except Exception as e:
                print(f"❌ Błąd aktualizacji Firestore dla ID {sprzet_id}: {e}")

    print(f"\n--- ZAKOŃCZONO. Przesłano/zaktualizowano {uploaded_count} dokumentów. ---")


if __name__ == '__main__':
    upload_and_update_firestore()
