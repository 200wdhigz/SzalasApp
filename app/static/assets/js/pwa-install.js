// PWA Installation Handler
let deferredPrompt;
const installButton = document.getElementById('pwa-install-button');

// Nasłuchuj na zdarzenie beforeinstallprompt
window.addEventListener('beforeinstallprompt', (e) => {
  // Zapobiegaj domyślnemu wyświetlaniu banera instalacji
  e.preventDefault();
  // Zapisz zdarzenie na później
  deferredPrompt = e;

  // Pokaż przycisk instalacji (jeśli istnieje)
  if (installButton) {
    installButton.style.display = 'block';
  }

  console.log('PWA: Install prompt available');
});

// Obsługa kliknięcia przycisku instalacji
if (installButton) {
  installButton.addEventListener('click', async () => {
    if (!deferredPrompt) {
      return;
    }

    // Pokaż prompt instalacji
    deferredPrompt.prompt();

    // Czekaj na wybór użytkownika
    const { outcome } = await deferredPrompt.userChoice;
    console.log(`PWA: User response to install prompt: ${outcome}`);

    // Wyczyść deferredPrompt
    deferredPrompt = null;

    // Ukryj przycisk
    installButton.style.display = 'none';
  });
}

// Rejestracja Service Workera
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then((registration) => {
        console.log('PWA: Service Worker registered successfully:', registration.scope);

        // Sprawdź aktualizacje co godzinę
        setInterval(() => {
          registration.update();
        }, 3600000);
      })
      .catch((err) => {
        console.error('PWA: Service Worker registration failed:', err);
      });
  });
}

// Wykryj czy aplikacja jest zainstalowana
window.addEventListener('appinstalled', () => {
  console.log('PWA: App installed successfully');
  if (installButton) {
    installButton.style.display = 'none';
  }
});

// Sprawdź czy aplikacja jest uruchomiona jako PWA
function isPWA() {
  return window.matchMedia('(display-mode: standalone)').matches ||
         window.navigator.standalone === true;
}

if (isPWA()) {
  console.log('PWA: Running as installed app');
  document.body.classList.add('pwa-mode');
}

