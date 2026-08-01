"""Bingo rules: sessions, cards, draws and winning."""

import random
from datetime import timedelta, timezone

from flask import current_app

from .extensions import db
from .models import Card, Draw, GameSession, utcnow

NUMBER_MIN = 10
NUMBER_MAX = 99
CARD_SIZE = 9


def active_session():
    """The single open session, created on first use."""
    session = (
        GameSession.query.filter_by(ended_at=None)
        .order_by(GameSession.id.desc())
        .first()
    )
    if session is None:
        session = GameSession()
        db.session.add(session)
        db.session.commit()
    return session


def new_card_numbers():
    """Nine unique numbers between 10 and 99.

    Unique *within* one card only. Two players can both hold 33; a single player
    can never hold 33 twice.
    """
    return sorted(random.sample(range(NUMBER_MIN, NUMBER_MAX + 1), CARD_SIZE))


def get_or_create_card(session, user):
    card = Card.query.filter_by(session_id=session.id, user_id=user.id).first()
    if card is None:
        card = Card(
            session_id=session.id,
            user_id=user.id,
            numbers=new_card_numbers(),
            marked=[False] * CARD_SIZE,
        )
        db.session.add(card)
        db.session.commit()
    return card


def drawn_numbers(session):
    """All numbers drawn in this session, newest first."""
    return (
        Draw.query.filter_by(session_id=session.id)
        .order_by(Draw.created_at.desc(), Draw.id.desc())
        .all()
    )


def add_draw(session, user, number):
    """Register a drawn number. Returns (ok, message)."""
    if session.winner_id is not None or session.winner_name:
        return False, "Deze sessie is al gewonnen. Wacht tot de beheerder reset."
    if not (NUMBER_MIN <= number <= NUMBER_MAX):
        return False, f"Alleen nummers van {NUMBER_MIN} tot en met {NUMBER_MAX}."
    existing = Draw.query.filter_by(session_id=session.id, number=number).first()
    if existing is not None:
        return False, f"{number} is al getrokken."

    cooldown = current_app.config.get("DRAW_COOLDOWN_SECONDS", 0)
    if cooldown:
        last = (
            Draw.query.filter_by(session_id=session.id, user_id=user.id)
            .order_by(Draw.created_at.desc())
            .first()
        )
        if last is not None:
            # SQLite hands back naive datetimes; they were stored as UTC.
            since = utcnow() - last.created_at.replace(tzinfo=timezone.utc)
            if since < timedelta(seconds=cooldown):
                wait = int((timedelta(seconds=cooldown) - since).total_seconds()) + 1
                return False, f"Nog even geduld: over {wait} seconden mag je weer."

    db.session.add(
        Draw(
            session_id=session.id,
            number=number,
            user_id=user.id,
            user_name=user.name,
        )
    )
    db.session.commit()
    return True, f"{number} toegevoegd aan de trekking."


def toggle_mark(session, card, index):
    """Mark or unmark one square. Returns (ok, message)."""
    if not (0 <= index < CARD_SIZE):
        return False, "Onbekend vakje."
    if session.winner_name:
        return False, "Deze sessie is al gewonnen."

    marked = list(card.marked)
    if marked[index]:
        marked[index] = False
        card.marked = marked
        db.session.commit()
        return True, "Vakje weer vrijgegeven."

    number = card.numbers[index]
    is_drawn = (
        Draw.query.filter_by(session_id=session.id, number=number).first() is not None
    )
    if not is_drawn:
        return False, f"{number} is nog niet getrokken."

    marked[index] = True
    card.marked = marked
    db.session.commit()
    check_winner(session, card)
    return True, f"{number} afgestreept."


def check_winner(session, card):
    """Record the winner if this card just became full."""
    if session.winner_name or not card.is_full:
        return False
    session.winner_id = card.user_id
    session.winner_name = card.user.name
    session.won_at = utcnow()
    db.session.commit()
    return True


def ranking(session, limit=None):
    """Players in this session ordered by number of marked squares."""
    cards = Card.query.filter_by(session_id=session.id).all()
    rows = [
        {"name": c.user.name, "count": c.marked_count}
        for c in cards
        if c.user is not None
    ]
    rows.sort(key=lambda r: (-r["count"], r["name"].lower()))
    return rows[:limit] if limit else rows


def reset_session():
    """Close the running session and open a fresh one. Nothing is deleted."""
    current = active_session()
    current.ended_at = utcnow()
    db.session.add(GameSession())
    db.session.commit()
