"""Bazanın yaradılması, yumşaq miqrasiya və ilkin məlumatlar.

Mövcud məlumatlar heç vaxt silinmir: cədvəllər yalnız olmadıqda yaradılır,
yeni sütunlar ``ADD COLUMN IF NOT EXISTS`` ilə əlavə olunur. Tək müsabiqəli
köhnə versiyadan gələn bütün komanda, meyar, jüri və ballar ilk müsabiqəyə
bağlanır.
"""

import logging

from sqlalchemy import func, select, text

from .config import settings
from .db import Base, SessionLocal, engine
from .models import Contest, Criterion, Team, User
from .security import hash_password, validate_password

log = logging.getLogger("portal")

DEFAULT_CRITERIA = ["İnnovativlik", "Təsir", "İcra oluna bilmə", "Dayanıqlılıq", "Təqdimat"]


def _add_contest_fk(table: str, nullable: bool, jury_only: bool = False) -> list[str]:
    where = "contest_id IS NULL" + (" AND role = 'jury'" if jury_only else "")
    stmts = [
        f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS contest_id INTEGER",
        f"UPDATE {table} SET contest_id = (SELECT min(id) FROM contest) WHERE {where}",
        f"CREATE INDEX IF NOT EXISTS ix_{table}_contest_id ON {table} (contest_id)",
        f"""DO $$ BEGIN
              IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{table}_contest_id_fkey') THEN
                ALTER TABLE {table} ADD CONSTRAINT {table}_contest_id_fkey
                  FOREIGN KEY (contest_id) REFERENCES contest(id) ON DELETE CASCADE;
              END IF;
            END $$""",
    ]
    if not nullable:
        stmts.append(f"ALTER TABLE {table} ALTER COLUMN contest_id SET NOT NULL")
    return stmts


# Köhnə versiyalardan gələn bazalar üçün idempotent əlavələr.
_MIGRATIONS = [
    # --- v1 (tək müsabiqə) sahələri
    "ALTER TABLE contest ADD COLUMN IF NOT EXISTS eval_type VARCHAR(16) NOT NULL DEFAULT 'unique'",
    "ALTER TABLE contest ADD COLUMN IF NOT EXISTS custom_max INTEGER",
    "ALTER TABLE contest ADD COLUMN IF NOT EXISTS structure_locked BOOLEAN NOT NULL DEFAULT false",
    "ALTER TABLE contest ADD COLUMN IF NOT EXISTS locked_at TIMESTAMPTZ",
    "ALTER TABLE contest ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1",
    "UPDATE contest SET eval_type = 'unique' WHERE eval_type IS NULL OR eval_type = ''",
    "ALTER TABLE scores ADD COLUMN IF NOT EXISTS unique_scope BOOLEAN NOT NULL DEFAULT false",
    "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS edited_at TIMESTAMPTZ",
    "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1",
    # --- v2: bir neçə müsabiqə
    "ALTER TABLE contest DROP CONSTRAINT IF EXISTS ck_contest_single",
    # Mövcud müsabiqə açıq qalır (əvvəlki davranış); yenilər bağlı yaradılır.
    "ALTER TABLE contest ADD COLUMN IF NOT EXISTS is_open BOOLEAN NOT NULL DEFAULT true",
    "ALTER TABLE contest ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now()",
    # Köhnə cədvəldə id üçün ardıcıllıq yox idi.
    "CREATE SEQUENCE IF NOT EXISTS contest_id_seq OWNED BY contest.id",
    "SELECT setval('contest_id_seq', COALESCE((SELECT max(id) FROM contest), 0) + 1, false)",
    "ALTER TABLE contest ALTER COLUMN id SET DEFAULT nextval('contest_id_seq')",
    *_add_contest_fk("teams", nullable=False),
    *_add_contest_fk("criteria", nullable=False),
    *_add_contest_fk("evaluations", nullable=False),
    *_add_contest_fk("users", nullable=True, jury_only=True),
    "ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS contest_id INTEGER",
    "CREATE INDEX IF NOT EXISTS ix_audit_log_contest_id ON audit_log (contest_id)",
    # Artıq bal verilmiş müsabiqənin strukturu kilidli olmalıdır.
    "UPDATE contest c SET structure_locked = true, locked_at = COALESCE(locked_at, now()) "
    "WHERE structure_locked = false AND EXISTS (SELECT 1 FROM evaluations e WHERE e.contest_id = c.id)",
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
        if not db.scalar(select(func.count(Contest.id))):
            create_contest(db, "Müsabiqə", "unique", None, seed=settings.seed_demo, is_open=True)
        bootstrap_admin(db)
        db.commit()


def create_contest(db, name: str, eval_type: str, custom_max: int | None, *, seed: bool,
                   teams: int = 10, is_open: bool = False) -> Contest:
    c = Contest(name=name, eval_type=eval_type, custom_max=custom_max, is_open=is_open)
    db.add(c)
    db.flush()
    if seed:
        for i in range(1, teams + 1):
            db.add(Team(contest_id=c.id, name=f"Komanda {i:02d}", position=i))
        for i, cname in enumerate(DEFAULT_CRITERIA, start=1):
            db.add(Criterion(contest_id=c.id, name=cname, position=i))
    return c


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
