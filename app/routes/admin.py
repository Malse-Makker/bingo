"""Admin page: approve and remove users, reset the session, view statistics."""

from functools import wraps

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session as flask_session,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import func

from .. import game
from ..extensions import db
from ..models import Draw, GameSession, User
from ..passwords import generate_password, hash_password

bp = Blueprint("admin", __name__, url_prefix="/beheer")


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapper


@bp.get("/")
@admin_required
def index():
    session = game.active_session()
    return render_template(
        "beheer.html",
        sessie=session,
        wachtenden=User.query.filter_by(is_approved=False)
        .order_by(User.created_at)
        .all(),
        gebruikers=User.query.filter_by(is_approved=True)
        .order_by(User.name)
        .all(),
        ranglijst=game.ranking(session),
        trekkingen=game.drawn_numbers(session),
        scorebord=_all_time_scoreboard(),
        nummerstats=_number_stats(),
        # Popped so a reset password is shown exactly once, and never lands in
        # a URL or the browser history.
        nieuw_wachtwoord=flask_session.pop("nieuw_wachtwoord", None),
        nieuw_voor=flask_session.pop("nieuw_wachtwoord_voor", None),
    )


@bp.post("/goedkeuren/<int:user_id>")
@admin_required
def approve(user_id):
    user = db.get_or_404(User, user_id)
    user.is_approved = True
    db.session.commit()
    flash(f"{user.name} is goedgekeurd.", "success")
    return redirect(url_for("admin.index"))


@bp.post("/verwijderen/<int:user_id>")
@admin_required
def delete(user_id):
    user = db.get_or_404(User, user_id)
    if user.is_admin:
        flash("De beheerder kan niet verwijderd worden.", "error")
        return redirect(url_for("admin.index"))
    name = user.name
    db.session.delete(user)
    db.session.commit()
    flash(f"{name} is verwijderd.", "success")
    return redirect(url_for("admin.index"))


@bp.post("/wachtwoord/<int:user_id>")
@admin_required
def reset_password(user_id):
    user = db.get_or_404(User, user_id)
    password = generate_password()
    user.password_hash = hash_password(password)
    db.session.commit()
    # Shown once on the admin page so it can be passed on to the player.
    flask_session["nieuw_wachtwoord"] = password
    flask_session["nieuw_wachtwoord_voor"] = user.name
    return redirect(url_for("admin.index"))


@bp.post("/reset-sessie")
@admin_required
def reset_session():
    if request.form.get("bevestig") != "ja":
        flash("Reset geannuleerd.", "info")
        return redirect(url_for("admin.index"))
    game.reset_session()
    flash("Nieuwe sessie gestart. Iedereen krijgt een nieuwe kaart.", "success")
    return redirect(url_for("admin.index"))


def _all_time_scoreboard():
    """Wins per player across every session, including archived ones."""
    rows = (
        db.session.query(
            GameSession.winner_name, func.count(GameSession.id).label("aantal")
        )
        .filter(GameSession.winner_name.isnot(None))
        .group_by(GameSession.winner_name)
        .order_by(func.count(GameSession.id).desc(), GameSession.winner_name)
        .all()
    )
    return [{"naam": r[0], "aantal": r[1]} for r in rows]


def _number_stats():
    """How often each number was drawn, across all sessions."""
    rows = (
        db.session.query(Draw.number, func.count(Draw.id).label("aantal"))
        .group_by(Draw.number)
        .order_by(func.count(Draw.id).desc(), Draw.number)
        .all()
    )
    return [{"nummer": r[0], "aantal": r[1]} for r in rows]
