FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Fayllar həm qovluqlarla (app/...), həm də düz siyahı kimi yüklənibsə işləyir.
COPY . /tmp/src
RUN set -e; \
    if [ -f /tmp/src/app/main.py ]; then \
      cp -r /tmp/src/app /srv/app; \
    else \
      mkdir -p /srv/app/static/fonts; \
      cd /tmp/src; \
      for f in __init__.py cli.py config.py db.py logic.py main.py models.py routes_admin.py routes_auth.py routes_jury.py schemas.py security.py setup_db.py; do cp "$f" /srv/app/; done; \
      for f in app.js styles.css index.html favicon.svg; do cp "$f" /srv/app/static/; done; \
      cp inter-latin-wght-normal.woff2 inter-latin-ext-wght-normal.woff2 /srv/app/static/fonts/; \
      if [ -f OFL.txt ]; then cp OFL.txt /srv/app/static/fonts/; fi; \
    fi; \
    rm -rf /tmp/src; \
    useradd --create-home --uid 10001 portal && chown -R portal /srv
USER portal

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request,os; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/api/health')" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers ${WEB_CONCURRENCY:-2} --proxy-headers --forwarded-allow-ips='*'"]
