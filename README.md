# Makkers Bingo

A small bingo web app for a group of friends. Every player gets a 3x3 card with
nine random numbers between 10 and 99. Numbers enter the game when a player
types in a code they got from one of the two authenticator apps. Once a number
is in the session everyone holding it may cross it off. The first player with a
full card wins, and everyone gets a popup with confetti.

Runs at [bingo.makkers.net](https://bingo.makkers.net). The interface is in
Dutch; the code and this README are in English.

## Features

### Accounts

- **Registration**: you pick a name, the app picks the password. The password is
  one of the configured words repeated three times (`schaap` becomes
  `schaapschaapschaap`) and is shown exactly once, right after registering.
- **Approval**: a new account cannot log in until the admin approves it.
- **Admin account**: created on first start from `ADMIN_NAME` and
  `ADMIN_PASSWORD`. The admin has both the admin page and a normal player card.
- **Forgotten password**: the admin assigns a new word password and sees it once
  on the admin page. Passwords are stored hashed and are never recoverable.
- **Stay logged in**: the session cookie lasts 30 days, so phones do not have to
  log in every time.

### Playing

- **The card**: nine unique numbers between 10 and 99, generated per session.
  Unique *within* a card only, so two players can both hold 33 while a single
  player never holds it twice.
- **Adding a number**: type a number between 10 and 99 to add it to the session
  draw. Duplicates are refused, and the list shows who entered what.
- **Crossing off**: tap a square to mark it. A number that has not been drawn in
  this session cannot be marked. Tap again to undo a mistake.
- **Highlight**: a square whose number has been drawn but not yet crossed off
  pulses, so nobody misses their turn.
- **Live**: the page polls every three seconds, so drawn numbers, the ranking
  and the winner appear without reloading.
- **Top 3**: the three players with the most marked squares in this session.
- **Winning**: the first full card wins. Everyone sees `HOERA! <naam> heeft
  gewonnen!` with confetti, and the session locks until the admin resets it.

### Admin page

- Approve waiting accounts and delete accounts.
- Assign a new password to a player.
- Reset the session, behind a confirmation. Resetting closes the current session
  and opens a new one; nothing is deleted, so history stays intact.
- Standings for the current session.
- All-time scoreboard: who won the most sessions.
- Number statistics: how often every number was drawn across all sessions.

### Mobile / PWA

A web app manifest and a small service worker make the app installable on a
phone home screen, running full screen. Static assets are cached; game state is
always fetched from the network so it is never stale.

### Theme

Catppuccin Latte (light) and Frappe (dark). The system preference decides by
default; the button in the header cycles through auto, light and dark.

## Installation

### With Docker (production)

```bash
git clone git@github.com:Malse-Makker/bingo.git
cd bingo
cp .env.example .env
# Fill in SECRET_KEY, ADMIN_PASSWORD and PASSWORD_WORDS
docker compose up -d --build
```

Nginx listens on `BINGO_PORT` (9877 by default). TLS and the public hostname are
handled upstream by Nginx Proxy Manager, so nothing in this project terminates
TLS.

### Locally (development)

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cp .env.example .env      # set COOKIE_SECURE=0 for plain HTTP
./venv/bin/python run.py
```

The app is then at http://127.0.0.1:5000.

## Configuration

All settings come from `.env`, which is never committed.

| Variable | Meaning |
| --- | --- |
| `SECRET_KEY` | Required. Signs the session cookie. Generate with `openssl rand -hex 32`. |
| `ADMIN_NAME` | Name of the built-in admin account. Default `mick`. |
| `ADMIN_PASSWORD` | Required. Password for that account, applied on first start. |
| `PASSWORD_WORDS` | Required. Comma-separated words; each becomes a password repeated three times. |
| `BINGO_PORT` | Host port for nginx. Default `9877`. |
| `DATA_PATH` | Where the SQLite database lives on the host. Default `./data`. |
| `COOKIE_SECURE` | `1` (default) for HTTPS, `0` for local plain HTTP. |
| `DRAW_COOLDOWN_SECONDS` | Seconds a player must wait between entering two numbers. `0` disables it. |

The password list lives in `.env` on purpose: the passwords are meant to be easy
to remember, not secret, and they should not end up in a public repository.

## Security

The app is a hobby project for a closed group, but it still follows the usual
baseline: CSRF protection on every form, hashed passwords, rate limiting on
login and registration, `HttpOnly` / `SameSite` / `Secure` cookies, a
`Content-Security-Policy` without inline scripts or styles, and the standard
nginx security headers. Everything is served from the app's own origin; Font
Awesome is vendored locally.

There is no technical barrier against a player entering their own card numbers.
That is a deliberate trade-off: the draw list shows who entered which number, so
the group can see it happen. `DRAW_COOLDOWN_SECONDS` adds a delay between
entries if that is not enough.

## Deployment

Every push to `main` triggers `.github/workflows/deploy.yml`, which SSHes to the
OVH server and rebuilds the containers there.

## Versioning

Semantic versioning, tracked in `VERSION`. The footer shows the version and the
short commit hash.

## Disclaimer

This project was built with the help of AI, as a personal hobby and learning
project: both to learn more about working with AI and about the subject of the
project itself. The CI/CD setup (automatic deployment through GitHub Actions) is
part of that learning process.
