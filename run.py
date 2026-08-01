"""Entry point for gunicorn and for local development."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load the .env next to this file, so the app can be started from any directory.
load_dotenv(Path(__file__).resolve().parent / ".env")

from app import create_app  # noqa: E402  (after load_dotenv)

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
