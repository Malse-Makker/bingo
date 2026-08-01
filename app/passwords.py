"""Generation of the easy-to-remember passwords.

The word list lives in the environment (PASSWORD_WORDS) so it never ends up in
the public repository. Each word is repeated three times, so the word "schaap"
becomes the password "schaapschaapschaap".
"""

import os
import secrets

from werkzeug.security import generate_password_hash

# Werkzeug defaults to scrypt, which needs an OpenSSL build that provides it.
# pbkdf2 is available everywhere, so hashes stay portable between the container
# and a local checkout.
HASH_METHOD = "pbkdf2:sha256"


def hash_password(password):
    return generate_password_hash(password, method=HASH_METHOD)


def load_words():
    """Return the configured word list. Raises if it is missing or empty."""
    raw = os.environ.get("PASSWORD_WORDS", "")
    words = [w.strip().lower() for w in raw.split(",") if w.strip()]
    if not words:
        raise RuntimeError(
            "PASSWORD_WORDS is empty. Set a comma-separated word list in .env, "
            "for example: PASSWORD_WORDS=schaap,kat,hond"
        )
    return words


def all_passwords():
    """Every password that can be handed out, in the same order as the words."""
    return [w * 3 for w in load_words()]


def generate_password():
    """Pick one of the configured passwords at random.

    Two accounts can end up with the same password; that is fine here, logging
    in still needs the matching name.
    """
    return secrets.choice(all_passwords())
