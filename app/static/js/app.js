// Theme switch and service worker registration.
// Loaded without `defer` so the theme is applied before the first paint.

(function () {
  var OPTIES = ["auto", "licht", "donker"];

  function pas_toe(keuze) {
    if (keuze === "auto") {
      document.documentElement.removeAttribute("data-thema");
    } else {
      document.documentElement.setAttribute("data-thema", keuze);
    }
  }

  function huidig() {
    var opgeslagen = null;
    try {
      opgeslagen = localStorage.getItem("thema");
    } catch (e) {
      // Private mode: fall back to the system preference.
    }
    return OPTIES.indexOf(opgeslagen) >= 0 ? opgeslagen : "auto";
  }

  pas_toe(huidig());

  document.addEventListener("DOMContentLoaded", function () {
    var knop = document.getElementById("thema-knop");
    if (knop) {
      knop.addEventListener("click", function () {
        var volgende = OPTIES[(OPTIES.indexOf(huidig()) + 1) % OPTIES.length];
        try {
          localStorage.setItem("thema", volgende);
        } catch (e) {
          // Ignore: the theme then only lasts for this page view.
        }
        pas_toe(volgende);
        knop.title = "Thema: " + volgende;
      });
    }
  });

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/sw.js").catch(function () {
        // The app works fine without offline support.
      });
    });
  }
})();
