# Firebase - Konfiguracja
## 🔥 Wymagane Usługi
### 1. Firebase Authentication
- Email/Password
- Google OAuth (opcjonalnie)
- Microsoft OAuth (opcjonalnie)
### 2. Firestore Database
- Kolekcje: users, sprzet, usterki
- Rules: Production mode
- Lokalizacja: europe-central2 (zalecane)
### 3. Cloud Storage
- Bucket: default
- Zdjęcia sprzętu i usterek
- Public read (konfiguracja rules)
## Konfiguracja Rules
### Firestore Rules
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read: if request.auth != null;
      allow write: if request.auth != null && 
                      get(/databases//documents/users/).data.is_admin == true;
    }
  }
}
```
### Storage Rules
```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /{allPaths=**} {
      allow read: if true;
      allow write: if request.auth != null;
    }
  }
}
```
---
**Ostatnia aktualizacja:** 2026-01-01
