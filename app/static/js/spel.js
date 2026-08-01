// Player page: submits marks and numbers without a page reload, and polls the
// server so drawn numbers, the ranking and the winner appear for everyone.

(function () {
  var script = document.currentScript;
  var STATUS_URL = script.dataset.statusUrl;
  var IK = script.dataset.ik;
  var laatste_winnaar = script.dataset.winnaar || null;

  var csrf = document.querySelector('meta[name="csrf-token"]').content;
  var kaart = document.getElementById("bingokaart");
  var lijst_trekkingen = document.getElementById("trekkingen");
  var lijst_rang = document.getElementById("ranglijst");
  var meldingen = document.getElementById("meldingen");
  var overlay = document.getElementById("winnaar-overlay");

  function meld(tekst, soort) {
    meldingen.textContent = "";
    var p = document.createElement("p");
    p.className = "melding melding-" + soort;
    p.textContent = tekst;
    meldingen.appendChild(p);
  }

  function post(url, data) {
    return fetch(url, {
      method: "POST",
      headers: { "X-CSRFToken": csrf, "X-Requested-With": "fetch" },
      body: data,
    }).then(function (r) {
      return r.json();
    });
  }

  function verwerk(status) {
    if (!status || !status.kaart) return;

    var getrokken = status.trekkingen.map(function (t) {
      return t.nummer;
    });

    Array.prototype.forEach.call(kaart.querySelectorAll(".vakje"), function (vakje) {
      var i = parseInt(vakje.dataset.index, 10);
      var nummer = parseInt(vakje.dataset.nummer, 10);
      var gemarkeerd = !!status.gemarkeerd[i];
      vakje.classList.toggle("gemarkeerd", gemarkeerd);
      vakje.classList.toggle(
        "beschikbaar",
        !gemarkeerd && getrokken.indexOf(nummer) >= 0
      );
    });

    lijst_trekkingen.textContent = "";
    if (status.trekkingen.length === 0) {
      lijst_trekkingen.appendChild(regel_leeg("Nog niets getrokken."));
    }
    status.trekkingen.forEach(function (t) {
      var li = document.createElement("li");
      li.appendChild(span("trek-nummer", t.nummer));
      li.appendChild(span("trek-door", t.door));
      li.appendChild(span("trek-tijd", t.tijd));
      lijst_trekkingen.appendChild(li);
    });

    lijst_rang.textContent = "";
    if (status.ranglijst.length === 0) {
      lijst_rang.appendChild(regel_leeg("Nog geen spelers."));
    }
    status.ranglijst.forEach(function (s) {
      var li = document.createElement("li");
      li.appendChild(span("", s.name));
      li.appendChild(span("telling", s.count + "/9"));
      lijst_rang.appendChild(li);
    });

    if (status.winnaar && status.winnaar !== laatste_winnaar) {
      laatste_winnaar = status.winnaar;
      toon_winnaar(status.winnaar);
    }
  }

  function span(klasse, tekst) {
    var el = document.createElement("span");
    if (klasse) el.className = klasse;
    el.textContent = tekst;
    return el;
  }

  function regel_leeg(tekst) {
    var li = document.createElement("li");
    li.className = "leeg";
    li.textContent = tekst;
    return li;
  }

  function toon_winnaar(naam) {
    document.getElementById("winnaar-naam").textContent =
      naam === IK ? "Jij hebt gewonnen!" : naam + " heeft gewonnen!";
    overlay.hidden = false;
    confetti();
    if (navigator.vibrate) navigator.vibrate([120, 60, 120, 60, 240]);
  }

  function confetti() {
    var doel = document.getElementById("confetti");
    var kleuren = ["--mauve", "--geel", "--groen", "--blauw", "--perzik", "--rood"];
    var stijl = getComputedStyle(document.documentElement);
    doel.textContent = "";
    for (var i = 0; i < 80; i++) {
      var s = document.createElement("span");
      s.className = "snipper";
      s.style.left = Math.random() * 100 + "%";
      s.style.background = stijl.getPropertyValue(
        kleuren[i % kleuren.length]
      );
      s.style.animationDuration = 2.5 + Math.random() * 2.5 + "s";
      s.style.animationDelay = Math.random() * 1.5 + "s";
      doel.appendChild(s);
    }
  }

  document.getElementById("winnaar-sluiten").addEventListener("click", function () {
    overlay.hidden = true;
    document.getElementById("confetti").textContent = "";
  });

  // Marking a square.
  Array.prototype.forEach.call(document.querySelectorAll(".js-markeer"), function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      post(form.action, new FormData(form)).then(function (r) {
        if (!r.ok) meld(r.bericht, "error");
        else meldingen.textContent = "";
        verwerk(r);
      });
    });
  });

  // Adding a drawn number.
  var nummer_form = document.querySelector(".js-nummer");
  nummer_form.addEventListener("submit", function (e) {
    e.preventDefault();
    var veld = nummer_form.querySelector('input[name="nummer"]');
    post(nummer_form.action, new FormData(nummer_form)).then(function (r) {
      meld(r.bericht, r.ok ? "success" : "error");
      if (r.ok) veld.value = "";
      verwerk(r);
      veld.focus();
    });
  });

  function ophalen() {
    if (document.hidden) return;
    fetch(STATUS_URL, { headers: { "X-Requested-With": "fetch" } })
      .then(function (r) {
        return r.ok ? r.json() : null;
      })
      .then(verwerk)
      .catch(function () {
        // Offline or restarting: the next poll picks it up again.
      });
  }

  setInterval(ophalen, 3000);
  document.addEventListener("visibilitychange", ophalen);
  ophalen();
})();
