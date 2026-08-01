# Makkers Bingo

Een leuke bingo-app om met vrienden te spelen. Iedere speler krijgt een
3x3-kaart met negen willekeurige nummers tussen de 10 en 99. Zodra iemand een
nummer intikt staat het in de trekking van de sessie, en mag iedereen die het op
zijn kaart heeft het afstrepen. Wie als eerste een volle kaart heeft wint, en
iedereen krijgt een popup met confetti.

Draait op [bingo.makkers.net](https://bingo.makkers.net). De interface en deze
README zijn in het Nederlands, de code zelf is in het Engels.

## Functies

### Accounts

- **Registreren**: jij verzint een naam, de app kiest het wachtwoord. Dat
  wachtwoord is een van de ingestelde woorden, drie keer achter elkaar
  (`schaap` wordt `schaapschaapschaap`), en je ziet het precies één keer: direct
  na het registreren.
- **Goedkeuren**: een nieuw account kan niet inloggen tot de beheerder het
  heeft goedgekeurd.
- **Beheerdersaccount**: wordt bij de eerste start aangemaakt uit `ADMIN_NAME`
  en `ADMIN_PASSWORD`. De beheerder heeft zowel de beheerpagina als een gewone
  eigen bingokaart.
- **Wachtwoord kwijt**: de beheerder wijst een nieuw dier-wachtwoord toe en ziet
  dat één keer op de beheerpagina. Wachtwoorden staan gehasht opgeslagen en zijn
  nooit terug te lezen.
- **Ingelogd blijven**: de sessiecookie is 30 dagen geldig, zodat je op je
  telefoon niet steeds opnieuw hoeft in te loggen.

### Spelen

- **De kaart**: negen unieke nummers tussen 10 en 99, per sessie opnieuw
  gegenereerd. Uniek *binnen* een kaart, dus twee spelers kunnen allebei 33
  hebben terwijl één speler 33 nooit dubbel heeft.
- **Nummer toevoegen**: tik een nummer tussen 10 en 99 in om het aan de trekking
  van de sessie toe te voegen. Dubbele nummers worden geweigerd, en in de lijst
  staat wie welk nummer heeft ingevoerd.
- **Afstrepen**: tik op een vakje om het te markeren. Een nummer dat nog niet
  getrokken is kun je niet afstrepen. Nog een keer tikken maakt een vergissing
  ongedaan.
- **Highlight**: een vakje waarvan het nummer wel getrokken maar nog niet
  afgestreept is, knippert. Zo mist niemand zijn beurt.
- **Live**: de pagina haalt elke drie seconden de stand op, dus getrokken
  nummers, de ranglijst en de winnaar verschijnen zonder verversen.
- **Top 3**: de drie spelers met de meeste afgestreepte vakjes in deze sessie.
- **Winnen**: de eerste volle kaart wint. Iedereen ziet `HOERA! <naam> heeft
  gewonnen!` met confetti, en de sessie gaat op slot tot de beheerder reset.

### Beheerpagina

- Wachtende accounts goedkeuren en accounts verwijderen.
- Een speler een nieuw wachtwoord geven.
- De sessie resetten, achter een bevestiging. Resetten sluit de huidige sessie
  af en start een nieuwe; er wordt niets weggegooid, dus de historie blijft
  kloppen.
- De stand van de huidige sessie.
- Scorebord aller tijden: wie heeft de meeste sessies gewonnen.
- Nummerstatistiek: hoe vaak elk nummer over alle sessies is getrokken.

### Mobiel / PWA

Een web app manifest en een kleine service worker maken de app installeerbaar op
je startscherm, schermvullend. Statische bestanden worden gecachet; de
spelstand komt altijd van de server, dus die is nooit verouderd.

### Thema

Catppuccin Latte (licht) en Frappe (donker). Standaard bepaalt je
systeeminstelling het thema; de knop in de balk wisselt tussen automatisch,
licht en donker.

## Installatie

### Met Docker (productie)

```bash
git clone git@github.com:Malse-Makker/bingo.git
cd bingo
cp .env.example .env
# Vul SECRET_KEY, ADMIN_PASSWORD en PASSWORD_WORDS in
docker compose up -d --build
```

Nginx luistert op `BINGO_PORT` (standaard 8123). TLS en de publieke hostnaam
regelt Nginx Proxy Manager ervoor, dus dit project doet zelf niets met TLS.

### Lokaal (ontwikkelen)

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cp .env.example .env      # zet COOKIE_SECURE=0 voor gewone HTTP
./venv/bin/python run.py
```

De app draait dan op http://127.0.0.1:5000.

## Instellingen

Alle instellingen komen uit `.env`, dat nooit in de repository terechtkomt.

| Variabele | Betekenis |
| --- | --- |
| `SECRET_KEY` | Verplicht. Ondertekent de sessiecookie. Maak er een met `openssl rand -hex 32`. |
| `ADMIN_NAME` | Naam van het ingebouwde beheerdersaccount. Standaard `mick`. |
| `ADMIN_PASSWORD` | Verplicht. Wachtwoord voor dat account, gezet bij de eerste start. |
| `PASSWORD_WORDS` | Verplicht. Woorden gescheiden door komma's; elk woord wordt drie keer herhaald tot een wachtwoord. |
| `BINGO_PORT` | Poort op de host waar nginx op luistert. Standaard `8123`. |
| `DATA_PATH` | Waar de SQLite-database op de host staat. Standaard `./data`. |
| `COOKIE_SECURE` | `1` (standaard) voor HTTPS, `0` voor lokaal via gewone HTTP. |
| `DRAW_COOLDOWN_SECONDS` | Aantal seconden dat een speler moet wachten tussen twee nummers. `0` zet het uit. |

De woordenlijst staat bewust in `.env`: de wachtwoorden horen makkelijk te
onthouden te zijn, niet geheim, en horen dus niet in een publieke repository.

## Beveiliging

Het is een hobbyproject voor een besloten groep, maar de gebruikelijke basis
staat er wel: CSRF-bescherming op elk formulier, gehashte wachtwoorden,
rate limiting op inloggen en registreren, `HttpOnly`- / `SameSite`- /
`Secure`-cookies, een `Content-Security-Policy` zonder inline scripts of styles,
en de standaard nginx security headers. Alles komt van de eigen origin; Font
Awesome staat lokaal in het project.

Er is geen technische drempel tegen een speler die zijn eigen kaartnummers
invoert. Dat is een bewuste afweging: in de trekkingslijst staat wie welk nummer
heeft ingevoerd, dus de groep ziet het gebeuren. Met
`DRAW_COOLDOWN_SECONDS` zet je er een wachttijd tussen als dat niet genoeg is.

## Uitrollen

Elke push naar `main` start `.github/workflows/deploy.yml`. Die SSH't naar de
OVH-server en bouwt de containers daar opnieuw.

## Versienummers

Semantic versioning, bijgehouden in `VERSION`. In de voettekst staan het
versienummer en de korte commit-hash.

## Disclaimer

Dit project is gemaakt met hulp van AI, als persoonlijk speel- en leerproject:
zowel om meer te leren over werken met AI als over het onderwerp van het project
zelf. De CI/CD-opzet (automatisch uitrollen via GitHub Actions) hoort bij dat
leerproces.
