# Laner Money: one small image, used by both the app and the backup job.
# Slim Debian + Python, runs as a non-root user, data lives in /data (a volume).
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    LANER_DB_PATH=/data/laner.db \
    LANER_BACKUP_DIR=/backups

# tzdata so TZ (e.g. Europe/London) works: "today" and backup times use it.
RUN apt-get update \
 && apt-get install -y --no-install-recommends tzdata \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/laner
# Dependencies first, so code changes don't reinstall them on every build.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Non-root user with no shell or home. It owns only /data and /backups;
# the code itself stays read-only to it.
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin laner \
 && mkdir /data /backups \
 && chown laner:laner /data /backups \
 && chmod 700 /data /backups

COPY app ./app

USER laner
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]

# No --reload, no debug, one process (the login rate limiter lives in memory).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
