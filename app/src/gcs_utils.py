import os
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError
from dotenv import load_dotenv

load_dotenv()

from . import GOOGLE_PROJECT_ID, GOOGLE_CLOUD_STORAGE_BUCKET_NAME

def get_storage_client():
    """Zwraca klienta Google Cloud Storage."""
    try:
        return storage.Client(project=GOOGLE_PROJECT_ID) if GOOGLE_PROJECT_ID else storage.Client()
    except DefaultCredentialsError:
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if credentials_path and os.path.exists(credentials_path):
            return storage.Client.from_service_account_json(credentials_path, project=GOOGLE_PROJECT_ID)
        raise Exception("Brak poświadczeń Google Cloud.")

import datetime

def extract_blob_name(url: str) -> str:
    """Wyciąga blob_name z URL GCS (usuwa parametry podpisu)."""
    if not url or not GOOGLE_CLOUD_STORAGE_BUCKET_NAME:
        return ""

    try:
        if 'storage.googleapis.com' in url:
            # Rozdzielamy po nazwie bucketa
            parts = url.split(f"{GOOGLE_CLOUD_STORAGE_BUCKET_NAME}/")
            if len(parts) > 1:
                blob_name = parts[1].split('?')[0]
                return blob_name
    except Exception:
        pass
    return ""

def generate_signed_url(blob_name: str) -> str:
    """Generuje Signed URL (V4) dla obiektu w GCS."""
    if not GOOGLE_CLOUD_STORAGE_BUCKET_NAME:
        return ""

    try:
        client = get_storage_client()
        bucket = client.bucket(GOOGLE_CLOUD_STORAGE_BUCKET_NAME)
        blob = bucket.blob(blob_name)

        url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(hours=1),
            method="GET",
        )
        return url
    except Exception as e:
        print(f"Error generating signed URL for {blob_name}: {e}")
        return f"https://storage.googleapis.com/{GOOGLE_CLOUD_STORAGE_BUCKET_NAME}/{blob_name}"

def upload_blob_to_gcs(blob_name: str, file_obj, mime_type: str) -> str:
    """Wgrywa obiekt do GCS i zwraca Signed URL."""
    if not GOOGLE_CLOUD_STORAGE_BUCKET_NAME:
        raise ValueError("GOOGLE_CLOUD_STORAGE_BUCKET_NAME nie jest ustawione.")

    client = get_storage_client()
    bucket = client.bucket(GOOGLE_CLOUD_STORAGE_BUCKET_NAME)
    blob = bucket.blob(blob_name)

    file_obj.seek(0)
    blob.upload_from_file(file_obj, content_type=mime_type, rewind=True)

    return generate_signed_url(blob_name)

def list_files(prefix: str) -> list:
    """Listuje pliki w GCS z danym prefiksem i zwraca ich Signed URLs."""
    if not GOOGLE_CLOUD_STORAGE_BUCKET_NAME:
        return []

    try:
        client = get_storage_client()
        bucket = client.bucket(GOOGLE_CLOUD_STORAGE_BUCKET_NAME)
        blobs = bucket.list_blobs(prefix=prefix)
        
        urls = []
        for blob in blobs:
            if not blob.name.endswith('/'):
                urls.append(generate_signed_url(blob.name))
        urls.sort()
        return urls
    except Exception as e:
        print(f"Error listing files with prefix {prefix}: {e}")
        return []

def refresh_urls(urls):
    """Odświeża sygnatury w liście URL-i GCS."""
    if not urls:
        return []
    
    new_urls = []
    for url in urls:
        if not url:
            continue
            
        blob_name = extract_blob_name(url)
        if blob_name:
            new_urls.append(generate_signed_url(blob_name))
        else:
            new_urls.append(url)
            
    return new_urls

def list_equipment_photos(equipment_id: str):
    """Listuje zdjęcia sprzętu."""
    return list_files(f"sprzet/{equipment_id.upper()}/")

def upload_defect_photos(defect_id: str, files: list) -> list:
    """Wgrywa zdjęcia usterki z zachowaniem konwencji nazw."""
    uploaded_urls = []
    valid_files = [f for f in files if f and f.filename]
    for i, file_obj in enumerate(valid_files):
        blob_name = f"usterki/{defect_id}/{defect_id}_foto{i:02d}.png"
        try:
            url = upload_blob_to_gcs(blob_name, file_obj.stream, file_obj.mimetype or 'image/png')
            uploaded_urls.append(url)
        except Exception as e:
            print(f"Failed to upload {blob_name}: {e}")
    return uploaded_urls