import os


def _normalize_db_url(url: str) -> str:
    # Render/Heroku kimi xidmətlər "postgres://" verir; SQLAlchemy + psycopg3 üçün çeviririk.
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


class Settings:
    def __init__(self) -> None:
        self.database_url = _normalize_db_url(
            os.environ.get("DATABASE_URL", "postgresql+psycopg://portal:portal@localhost:5432/portal")
        )
        # "auto": sorğu HTTPS ilə gəlibsə cookie Secure olur; "1" həmişə, "0" heç vaxt.
        self.cookie_secure = os.environ.get("COOKIE_SECURE", "auto").strip().lower()
        self.session_hours = int(os.environ.get("SESSION_HOURS", "12"))
        self.cookie_name = "qp_session"
        # İlkin admin yalnız heç bir admin olmadıqda bu dəyişənlərdən yaradılır.
        self.bootstrap_admin_username = os.environ.get("ADMIN_USERNAME", "").strip()
        self.bootstrap_admin_password = os.environ.get("ADMIN_PASSWORD", "")
        self.seed_demo = os.environ.get("SEED_DEFAULTS", "1") == "1"


settings = Settings()
