import firebase_admin
from firebase_admin import auth, credentials
import os
from dotenv import load_dotenv

load_dotenv()

TARGET_UID = "kCoy3SWwm6O2fgRUXgKUOhCimpI3"

def toggle_admin(uid, status=True):
    try:
        auth.set_custom_user_claims(uid, {'admin': status})
        print(f"Admin status for {uid} set to {status}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    if not firebase_admin._apps:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {'projectId': os.getenv('FIREBASE_PROJECT_ID')})
    
    toggle_admin(TARGET_UID)