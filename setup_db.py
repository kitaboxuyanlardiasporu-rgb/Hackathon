"""Bazanın yaradılması, yumşaq miqrasiya və ilkin məlumatlar.

Mövcud məlumatlar heç vaxt silinmir: cədvəllər yalnız olmadıqda yaradılır,
yeni sütunlar ``ADD COLUMN IF NOT EXISTS`` ilə əlavə olunur.
"""

import logging

from sqlalchemy import func, select, text

from .config import settings
from .db import Base, SessionLocal, engine
from .models import Contest, Criterion, Team, User
from .security import hash_password, validate_password

log = logging.getLogger("portal")

DEFAULT_CRITERIA = ["İnnovativlik", "Təsir", "İcra oluna bilmə", "Dayanıqlılıq", "Təqdimat"]

# Köhnə versiyalardan gələn bazalar üçün idempotent əlavələr.
_MIGRATIONS = [
    # Qiymətləndirmə tipi qeyd olunmamış mövcud müsabiqələr "Unikal bal" sayılır.
    "ALTER TABLE contest ADD COLUMN IF NOT EXISTS eval_type VARCHAR(16) NOT NULL DEFAULT 'unique'",
    "ALTER TABLE contest ADD COLUMN IF NOT EXISTS custom_max INTEGER",
    "ALTER TABLE contest ADD COLUMN IF NOT EXISTS structure_locked BOOLEAN NOT NULL DEFAULT false",
    "ALTER TABLE contest ADD COLUMN IF NOT EXISTS locked_at TIMESTAMPTZ",
    "ALTER TABLE contest ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1",
    "UPDATE contest SET eval_type = 'unique' WHERE eval_type IS NULL OR eval_type = ''",
    "ALTER TABLE scores ADD COLUMN IF NOT EXISTS unique_scope BOOLEAN NOT NULL DEFAULT false",
    "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS edited_at TIMESTAMPTZ",
    "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1",
    # Artıq bal verilmiş müsabiqənin strukturu kilidli olmalıdır.
    "UPDATE contest SET structure_locked = true, locked_at = COALESCE(locked_at, now()) "
    "WHERE structure_locked = false AND EXISTS (SELECT 1 FROM evaluations)",
]


def init_db() -> None:
    # Bir neçə proses eyni vaxtda başlasa, miqrasiyanı ardıcıl icra edirik.
    with engine.begin() as conn:
        conn.execute(text("SELECT pg_advisory_xact_lock(724501)"))
        Base.metadata.create_all(conn)
        for stmt in _MIGRATIONS:
            conn.execute(text(stmt))

    with SessionLocal() as db:
        db.execute(text("SELECT pg_advisory_xact_lock(724502)"))
        if db.get(Contest, 1) is None:
            db.add(Contest(id=1, name="Müsabiqə", eval_type="unique"))
            if settings.seed_demo and not db.scalar(select(func.count(Team.id))):
                for i in range(1, 11):
                    db.add(Team(name=f"Komanda {i:02d}", position=i))
            if settings.seed_demo and not db.scalar(select(func.count(Criterion.id))):
                for i, name in enumerate(DEFAULT_CRITERIA, start=1):
                    db.add(Criterion(name=name, position=i))
        bootstrap_admin(db)
        db.commit()


def bootstrap_admin(db) -> None:
    """ADMIN_USERNAME/ADMIN_PASSWORD yalnız heç bir admin olmadıqda istifadə olunur."""
    has_admin = db.scalar(select(func.count(User.id)).where(User.role == "admin"))
    if has_admin:
        return
    u, p = settings.bootstrap_admin_username, settings.bootstrap_admin_password
    if not u or not p:
        log.warning(
            "Admin hesabı yoxdur. 'python -m app.cli create-admin' əmri ilə və ya "
            "ADMIN_USERNAME/ADMIN_PASSWORD mühit dəyişənləri ilə yaradın."
        )
        return
    validate_password(p)
    db.add(User(username=u, password_hash=hash_password(p), role="admin"))
    log.warning("İlkin admin hesabı yaradıldı: %s", u)
