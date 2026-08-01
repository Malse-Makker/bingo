"""Application factory for the bingo app."""

import os
import secrets
from pathlib import Path

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .extensions import csrf, db, limiter, login_manager
from .passwords import hash_password

BASE_DIR = Path(__file__).resolve().parent.parent


def _read_version():
    version_file = BASE_DIR / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.0.0"


def _secret_key():
    key = os.environ.get("SECRET_KEY", "").strip()
    if key and key != "change-this-to-a-long-random-string":
        return key
    if os.environ.get("FLASK_ENV") == "development":
        # Ephemeral key for local development only: sessions die on restart.
        return secrets.token_hex(32)
    raise RuntimeError(
        "SECRET_KEY is missing or insecure. Generate one with: openssl rand -hex 32"
    )


def create_app():
    app = Flask(__name__)

    app.config.update(
        SECRET_KEY=_secret_key(),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'bingo.db'}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "1") == "1",
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "1") == "1",
        REMEMBER_COOKIE_DURATION=60 * 60 * 24 * 30,
        DRAW_COOLDOWN_SECONDS=int(os.environ.get("DRAW_COOLDOWN_SECONDS", "0")),
        ADMIN_NAME=os.environ.get("ADMIN_NAME", "mick").strip().lower(),
        APP_VERSION=_read_version(),
        GIT_COMMIT=os.environ.get("GIT_COMMIT", "")[:7],
        GITHUB_URL=os.environ.get(
            "GITHUB_URL", "https://github.com/Malse-Makker/bingo"
        ),
        PROJECTS_URL=os.environ.get("PROJECTS_URL", "https://projecten.makkers.net"),
    )

    # Behind Nginx Proxy Manager -> the app's own nginx -> gunicorn.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=2, x_proto=2, x_host=1)

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Log eerst in."
    login_manager.login_message_category = "info"

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from .routes.admin import bp as admin_bp
    from .routes.auth import bp as auth_bp
    from .routes.spel import bp as spel_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(spel_bp)
    app.register_blueprint(admin_bp)

    @app.context_processor
    def inject_globals():
        return {
            "admin_name": app.config["ADMIN_NAME"],
            "app_version": app.config["APP_VERSION"],
            "git_commit": app.config["GIT_COMMIT"],
            "github_url": app.config["GITHUB_URL"],
            "projects_url": app.config["PROJECTS_URL"],
        }

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    @app.route("/sw.js")
    def service_worker():
        # Must be served from the root so its scope covers the whole app.
        # In production nginx serves this file directly; this route keeps the
        # development server working too.
        response = app.send_static_file("js/sw.js")
        response.headers["Content-Type"] = "application/javascript"
        response.headers["Service-Worker-Allowed"] = "/"
        return response

    with app.app_context():
        db.create_all()
        _seed_admin()

    return app


def _seed_admin():
    """Create the built-in admin account on first start."""
    from .models import User

    from flask import current_app

    name = current_app.config["ADMIN_NAME"]
    password = os.environ.get("ADMIN_PASSWORD", "").strip()
    if not password:
        raise RuntimeError("ADMIN_PASSWORD is required.")

    admin = User.query.filter_by(name=name).first()
    if admin is None:
        admin = User(
            name=name,
            password_hash=hash_password(password),
            is_admin=True,
            is_approved=True,
        )
        db.session.add(admin)
        db.session.commit()
    elif not admin.is_admin or not admin.is_approved:
        admin.is_admin = True
        admin.is_approved = True
        db.session.commit()
