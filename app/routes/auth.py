"""Registration, login and logout."""

import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from ..extensions import db, limiter
from ..models import User
from ..passwords import generate_password, hash_password

bp = Blueprint("auth", __name__)

NAME_PATTERN = re.compile(r"^[a-z0-9 _-]{2,20}$")


def _clean_name(raw):
    return " ".join((raw or "").strip().lower().split())


@bp.route("/inloggen", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("spel.index"))

    if request.method == "POST":
        name = _clean_name(request.form.get("naam"))
        password = request.form.get("wachtwoord", "")
        user = User.query.filter_by(name=name).first()

        if user is None or not check_password_hash(user.password_hash, password):
            flash("Naam of wachtwoord klopt niet.", "error")
            return render_template("inloggen.html", naam=name), 401

        if not user.is_approved:
            flash(
                "Je account is nog niet goedgekeurd door de beheerder.", "info"
            )
            return render_template("inloggen.html", naam=name), 403

        login_user(user, remember=True)
        return redirect(url_for("spel.index"))

    return render_template("inloggen.html", naam="")


@bp.route("/registreren", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("spel.index"))

    if request.method == "POST":
        name = _clean_name(request.form.get("naam"))

        if not NAME_PATTERN.match(name):
            flash(
                "Kies een naam van 2 tot 20 tekens: letters, cijfers, spatie, - of _.",
                "error",
            )
            return render_template("registreren.html", naam=name), 400

        if User.query.filter_by(name=name).first() is not None:
            flash("Die naam is al bezet. Kies een andere.", "error")
            return render_template("registreren.html", naam=name), 400

        password = generate_password()
        user = User(
            name=name,
            password_hash=hash_password(password),
            is_admin=False,
            is_approved=False,
        )
        db.session.add(user)
        db.session.commit()

        # Shown exactly once: the plain password is never stored.
        return render_template("wachtwoord.html", naam=name, wachtwoord=password)

    return render_template("registreren.html", naam="")


@bp.route("/uitloggen", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Je bent uitgelogd.", "info")
    return redirect(url_for("auth.login"))
