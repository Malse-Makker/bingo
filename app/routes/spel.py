"""The player page: card, drawn numbers, ranking and the winner popup."""

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .. import game

bp = Blueprint("spel", __name__)


def _wants_json():
    return request.headers.get("X-Requested-With") == "fetch"


@bp.route("/")
@login_required
def index():
    if not current_user.is_approved:
        return render_template("wachten.html")

    session = game.active_session()
    card = game.get_or_create_card(session, current_user)
    return render_template(
        "spel.html",
        sessie=session,
        kaart=card,
        trekkingen=game.drawn_numbers(session),
        ranglijst=game.ranking(session, limit=3),
    )


@bp.post("/nummer")
@login_required
def add_number():
    if not current_user.is_approved:
        return redirect(url_for("spel.index"))

    session = game.active_session()
    raw = (request.form.get("nummer") or "").strip()
    try:
        number = int(raw)
    except ValueError:
        ok, message = False, "Vul een getal in."
    else:
        ok, message = game.add_draw(session, current_user, number)

    if _wants_json():
        return jsonify(ok=ok, bericht=message, **_state(session))
    flash(message, "success" if ok else "error")
    return redirect(url_for("spel.index"))


@bp.post("/markeer/<int:index>")
@login_required
def mark(index):
    if not current_user.is_approved:
        return redirect(url_for("spel.index"))

    session = game.active_session()
    card = game.get_or_create_card(session, current_user)
    ok, message = game.toggle_mark(session, card, index)

    if _wants_json():
        return jsonify(ok=ok, bericht=message, **_state(session))
    if not ok:
        flash(message, "error")
    return redirect(url_for("spel.index"))


@bp.get("/api/status")
@login_required
def status():
    if not current_user.is_approved:
        return jsonify(goedgekeurd=False), 403
    return jsonify(_state(game.active_session()))


def _state(session):
    """Everything the page polls for, in one payload."""
    card = game.get_or_create_card(session, current_user)
    return {
        "sessie": session.id,
        "kaart": card.numbers,
        "gemarkeerd": card.marked,
        "trekkingen": [
            {
                "nummer": d.number,
                "door": d.user_name or "verwijderd",
                "tijd": d.created_at.strftime("%H:%M"),
            }
            for d in game.drawn_numbers(session)
        ],
        "ranglijst": game.ranking(session, limit=3),
        "winnaar": session.winner_name,
    }
