"""Database models for the bingo app.

The data model keeps full history on purpose: resetting a session never deletes
anything, it only closes the current session and opens a new one. That keeps the
all-time scoreboard and the per-number draw statistics correct.
"""

from datetime import datetime, timezone

from flask_login import UserMixin

from .extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_approved = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    cards = db.relationship(
        "Card", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.name}>"


class GameSession(db.Model):
    """One round of bingo. Exactly one session has ended_at = NULL."""

    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    started_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)

    winner_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # Denormalised on purpose: the all-time scoreboard must survive the deletion
    # of the winning account.
    winner_name = db.Column(db.String(32), nullable=True)
    won_at = db.Column(db.DateTime, nullable=True)

    cards = db.relationship(
        "Card", back_populates="session", cascade="all, delete-orphan"
    )
    draws = db.relationship(
        "Draw", back_populates="session", cascade="all, delete-orphan"
    )

    @property
    def is_active(self):
        return self.ended_at is None


class Card(db.Model):
    """A single 3x3 bingo card: nine unique numbers for one user in one session."""

    __tablename__ = "cards"
    __table_args__ = (
        db.UniqueConstraint("session_id", "user_id", name="uq_card_session_user"),
    )

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer, db.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # Nine numbers (10-99), unique within this card but not across cards.
    numbers = db.Column(db.JSON, nullable=False)
    # Nine booleans, same order as `numbers`.
    marked = db.Column(db.JSON, nullable=False, default=lambda: [False] * 9)

    session = db.relationship("GameSession", back_populates="cards")
    user = db.relationship("User", back_populates="cards")

    @property
    def marked_count(self):
        return sum(1 for m in self.marked if m)

    @property
    def is_full(self):
        return self.marked_count == 9


class Draw(db.Model):
    """A number that was entered into the session by some user."""

    __tablename__ = "draws"
    __table_args__ = (
        db.UniqueConstraint("session_id", "number", name="uq_draw_session_number"),
    )

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer, db.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    number = db.Column(db.Integer, nullable=False)
    # Who entered it. Kept visible in the UI as social control against cheating.
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    user_name = db.Column(db.String(32), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    session = db.relationship("GameSession", back_populates="draws")
