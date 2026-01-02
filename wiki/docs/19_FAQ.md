# FAQ - Najczęściej Zadawane Pytania

## 🔐 Logowanie i Konta

### Q: Nie mogę się zalogować hasłem, ale mam konto Google/Microsoft połączone
**A:** To normalne! Jeśli masz połączone konto OAuth, użyj przycisku "Zaloguj przez Google" lub "Zaloguj przez Microsoft" zamiast hasła.

System pokaże komunikat: "To konto ma powiązane logowanie przez [Google/Microsoft]"

**Rozwiązanie:**
1. Kliknij odpowiedni przycisk OAuth
2. LUB ustaw hasło w "Moje Konto" → "Zmiana hasła"

### Q: Zapomniałem hasła
**A:** Skontaktuj się z administratorem. Admin może zresetować hasło i wysłać nowe na email.

### Q: Jak zmienić swoje hasło?
**A:**
1. Zaloguj się
2. "Moje Konto"
3. "Zmiana hasła"
4. Wprowadź obecne i nowe hasło
5. Zapisz

### Q: Mogę zmienić swój email?
**A:** Tak!
1. "Moje Konto"
2. "Zmiana adresu email"
3. Wprowadź nowy email i potwierdź hasłem
4. Zapisz

---

## 👥 Zarządzanie Użytkownikami

### Q: Kto może utworzyć nowe konto?
**A:** Tylko administratorzy. Nie ma samodzielnej rejestracji (bezpieczeństwo).

### Q: Jak zostać administratorem?
**A:** Tylko inny administrator może nadać uprawnienia admina.

### Q: Co się stanie jeśli usunę użytkownika?
**A:** 
- Użytkownik usunięty z Firebase Auth
- Usunięty z Firestore
- **Jego dane (sprzęt, usterki) pozostają**
- Operacja nieodwracalna

### Q: Dlaczego użytkownik widoczny po usunięciu w Firebase Console?
**A:** Musisz zsynchronizować listę. Kliknij "Synchronizuj" w panelu zarządzania użytkownikami.

---

## 📦 Sprzęt

### Q: Jak dodać nowy sprzęt?
**A:** 
- **Admin:** Ręcznie przez formularz lub import CSV/XLSX
- **Użytkownik:** Nie może (tylko admin)

### Q: Mogę zmienić ID sprzętu?
**A:** Nie. ID jest niezmienne. Musisz usunąć i utworzyć ponownie.

### Q: Limit zdjęć na sprzęt?
**A:** Brak limitu, ale upload max 5 naraz. Każde ≤5MB.

### Q: Jak usunąć zdjęcie ze sprzętu?
**A:** Obecnie tylko przez Firebase Console → Storage. Planujemy dodać do aplikacji.

### Q: Co to są kody QR?
**A:** Kody QR prowadzą do karty sprzętu. Możesz je wydrukować i nakleić na sprzęt dla szybkiego dostępu.

---

## 🔧 Usterki

### Q: Kto może zgłosić usterkę?
**A:** Każdy! Nie trzeba być zalogowanym (ale jest reCAPTCHA).

### Q: Jak długo czeka na odpowiedź?
**A:** Zależy od admina. Zwykle 1-3 dni. Pilne - zgłoś bezpośrednio.

### Q: Mogę edytować swoje zgłoszenie?
**A:** Nie. Po wysłaniu tylko admin może edytować.

### Q: Dostanę powiadomienie gdy naprawi?
**A:** Obecnie nie. Sprawdź status ręcznie. Planujemy email notifications.

### Q: Co oznaczają kolory statusów?
**A:**
- 🟡 Żółty (Oczekuje) - Nowe zgłoszenie
- 🔵 Niebieski (W trakcie) - Naprawa w toku
- 🟢 Zielony (Naprawiona) - Ukończone
- 🔴 Czerwony (Odrzucona) - Nieuzasadnione/duplikat

---

## 📊 Eksport

### Q: Jakie formaty eksportu są dostępne?
**A:** CSV, XLSX, DOCX, PDF

### Q: Czy eksport zawiera zdjęcia?
**A:** Nie, tylko linki URL do zdjęć.

### Q: Mogę eksportować tylko filtrowane dane?
**A:** Obecnie eksport pobiera wszystko. Filtry działają tylko w widoku.

---

## 🔒 Bezpieczeństwo

### Q: Czy moje hasło jest bezpieczne?
**A:** Tak. Hasła zarządzane przez Firebase Authentication (przemysłowy standard).

### Q: Co to reCAPTCHA?
**A:** Ochrona przed botami i spamem. Weryfikuje czy to człowiek zgłasza usterkę.

### Q: Czy admin widzi moje hasło?
**A:** Nie. Nikt nie widzi haseł (zahashowane). Admin może tylko zresetować.

---

## ⚙️ Techniczne

### Q: Dlaczego nie działa upload zdjęć?
**A:**
- Sprawdź rozmiar (max 5MB każde)
- Sprawdź format (tylko obrazy)
- Sprawdź limit (max 5 naraz)
- Sprawdź połączenie z internetem

### Q: Aplikacja jest wolna
**A:**
- Sprawdź połączenie z internetem
- Wyczyść cache przeglądarki
- Przeładuj stronę (Ctrl+F5)
- Sprawdź czy nie masz aktywnych filtrów

### Q: Widzę błąd 403 Forbidden
**A:** Brak uprawnień. Sprawdź czy jesteś zalogowany i masz odpowiednią rolę.

### Q: Nie przychodzą emaile z hasłami
**A:** Sprawdź:
- Folder SPAM
- Czy admin skonfigurował SMTP
- Czy email jest poprawny w profilu

---

## 🚀 Inne

### Q: Czy aplikacja działa offline?
**A:** Nie. Wymaga połączenia z internetem (Firebase, Cloud Storage).

### Q: Mogę używać na telefonie?
**A:** Tak! Aplikacja jest responsywna (dostosowuje się do ekranu).

### Q: Czy są aplikacje mobilne?
**A:** Obecnie nie. Używaj przeglądarki na telefonie.

### Q: Jak zgłosić bug?
**A:** Skontaktuj się z administratorem systemu lub zespołem rozwoju.

### Q: Gdzie jest dokumentacja?
**A:** W folderze `docs/` projektu lub pytaj admina o dostęp.

---

## 📞 Wsparcie

**Masz inne pytanie?**

1. Sprawdź dokumentację w `docs/`
2. Skontaktuj się z administratorem
3. Zgłoś issue na GitHub (jeśli masz dostęp)

---

**Ostatnia aktualizacja:** 2026-01-01  
**Wersja:** 1.0.0

