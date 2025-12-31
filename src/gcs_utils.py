# python
import os
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError
from dotenv import load_dotenv

load_dotenv()

GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')

def get_storage_client():
    """Zwraca klienta Google Cloud Storage."""
    try:
        return storage.Client(project=GCP_PROJECT_ID) if GCP_PROJECT_ID else storage.Client()
    except DefaultCredentialsError:
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if credentials_path and os.path.exists(credentials_path):
            return storage.Client.from_service_account_json(credentials_path, project=GCP_PROJECT_ID)
        raise Exception("Brak poświadczeń Google Cloud.")

def upload_blob_to_gcs(blob_name: str, file_obj, mime_type: str) -> str:
    """Wgrywa obiekt do GCS i zwraca publiczny URL."""
    if not GCS_BUCKET_NAME:
        raise ValueError("GCS_BUCKET_NAME nie jest ustawione.")

    client = get_storage_client()
    bucket = client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(blob_name)

    file_obj.seek(0)
    blob.upload_from_file(file_obj, content_type=mime_type, rewind=True)

    try:
        blob.make_public()
        return blob.public_url
    except Exception:
        return f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{blob_name}"

def list_files(prefix: str) -> list:
    """Listuje pliki w GCS z danym prefiksem."""
    if not GCS_BUCKET_NAME:
        return []

    try:
        client = get_storage_client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blobs = bucket.list_blobs(prefix=prefix)
        
        urls = []
        for blob in blobs:
            if not blob.name.endswith('/'):
                urls.append(blob.public_url or f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{blob.name}")
        urls.sort()
        return urls
    except Exception as e:
        print(f"Error listing files with prefix {prefix}: {e}")
        return []

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