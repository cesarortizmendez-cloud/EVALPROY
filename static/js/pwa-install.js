(function () {
  "use strict";

  const card = document.getElementById("pwaInstallCard");
  const installButton = document.getElementById("pwaInstallBtn");
  const dismissButton = document.getElementById("pwaDismissBtn");
  const iosHint = document.getElementById("pwaIosHint");
  const generalHint = document.getElementById("pwaGeneralHint");

  let deferredPrompt = null;

  function safeLocalStorageGet(key) {
    try {
      return window.localStorage.getItem(key);
    } catch (error) {
      return null;
    }
  }

  function safeLocalStorageSet(key, value) {
    try {
      window.localStorage.setItem(key, value);
    } catch (error) {
      // Algunos navegadores bloquean localStorage en modo privado.
    }
  }

  function isStandaloneMode() {
    return (
      window.matchMedia("(display-mode: standalone)").matches ||
      window.navigator.standalone === true
    );
  }

  function isIOSDevice() {
    return /iphone|ipad|ipod/i.test(window.navigator.userAgent);
  }

  function showCard() {
    if (!card || safeLocalStorageGet("evalproyPwaDismissed") === "true" || isStandaloneMode()) {
      return;
    }
    card.hidden = false;
  }

  function hideCard() {
    if (card) {
      card.hidden = true;
    }
  }

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/service-worker.js").catch(function () {
        // La aplicación sigue funcionando aunque el registro no esté disponible.
      });
    });
  }

  window.addEventListener("beforeinstallprompt", function (event) {
    event.preventDefault();
    deferredPrompt = event;

    if (installButton) {
      installButton.hidden = false;
    }
    if (generalHint) {
      generalHint.hidden = false;
    }
    if (iosHint) {
      iosHint.hidden = true;
    }

    showCard();
  });

  if (installButton) {
    installButton.addEventListener("click", async function () {
      if (!deferredPrompt) {
        if (isIOSDevice() && iosHint) {
          iosHint.hidden = false;
          showCard();
        }
        return;
      }

      deferredPrompt.prompt();
      await deferredPrompt.userChoice;
      deferredPrompt = null;
      hideCard();
    });
  }

  if (dismissButton) {
    dismissButton.addEventListener("click", function () {
      safeLocalStorageSet("evalproyPwaDismissed", "true");
      hideCard();
    });
  }

  window.addEventListener("appinstalled", function () {
    deferredPrompt = null;
    hideCard();
  });

  if (isIOSDevice() && !isStandaloneMode()) {
    if (installButton) {
      installButton.hidden = true;
    }
    if (generalHint) {
      generalHint.hidden = true;
    }
    if (iosHint) {
      iosHint.hidden = false;
    }
    showCard();
  }
})();
