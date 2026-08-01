FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as an unprivileged user; the data directory is a bind mount from the host.
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# One worker keeps the in-memory rate limiter and SQLite access simple.
CMD ["gunicorn", "-w", "1", "--threads", "4", "--bind", "0.0.0.0:8000", \
     "--timeout", "60", "--access-logfile", "-", "run:app"]
