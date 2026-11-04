import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import LoginThrottle, SessionToken, User

# ---------------------------------------------------------------- parollar
# scrypt (stdlib): hər parol üçün təsadüfi 16 baytlıq duz.
_N, _R, _P, _DKLEN = 2**14, 8, 1, 32


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_N, r=_R, p=_P, dklen=_DKLEN)
    return "scrypt${}${}${}${}${}".format(
        _N, _R, _P, base64.b64encode(salt).decode(), base64.b64encode(dk).decode()
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, n, r, p, salt_b64, dk_b64 = stored.split("$")
        if algo != "scrypt":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(dk_b64)
        dk = hashlib.scrypt(
            password.encode("utf-8"), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected)
        )
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


# Mövcud olmayan istifadəçi üçün də eyni müddətdə yoxlama aparmaq üçün.
DUMMY_HASH = hash_password(secrets.token_urlsafe(16))

PASSWORD_MIN = 8
PASSWORD_MAX = 128


def validate_password(pw: str) -> None:
    if not isinstance(pw, str) or len(pw) < PASSWORD_MIN:
        raise HTTPException(400, f"Parol ən azı {PASSWORD_MIN} simvoldan ibarət olmalıdır.")
    if len(pw) > PASSWORD_MAX:
        raise HTTPException(400, f"Parol ən çoxu {PASSWORD_MAX} simvol ola bilər.")


# ---------------------------------------------------------------- sessiyalar
def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def now() -> datetime:
    return datetime.now(timezone.utc)


def create_session(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    db.add(
        SessionToken(
            token_hash=_token_hash(token),
            user_id=user.id,
            expires_at=now() + timedelta(hours=settings.session_hours),
            last_seen=now(),
        )
    )
    return token


def _secure(request: Request | None) -> bool:
    mode = settings.cookie_secure
    if mode in ("1", "true", "yes"):
        return True
    if mode in ("0", "false", "no"):
        return False
    return bool(request is not None and request.url.scheme == "https")


def set_session_cookie(response, token: str, request: Request | None = None) -> None:
    response.set_cookie(
        settings.cookie_name,
        token,
        max_age=settings.session_hours * 3600,
        httponly=True,
        secure=_secure(request),
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response, request: Request | None = None) -> None:
    response.delete_cookie(settings.cookie_name, path="/", secure=_secure(request), httponly=True, samesite="lax")


def delete_session(db: Session, token: str | None) -> None:
    if token:
        s = db.get(SessionToken, _token_hash(token))
        if s:
            db.delete(s)


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(settings.cookie_name)
    if not token:
        raise HTTPException(401, "Sessiya bitib. Yenidən daxil olun.")
    s = db.get(SessionToken, _token_hash(token))
    t = now()
    if not s or s.expires_at <= t:
        if s:
            db.delete(s)
            db.commit()
        raise HTTPException(401, "Sessiya bitib. Yenidən daxil olun.")
    user = db.get(User, s.user_id)
    if not user or not user.active:
        raise HTTPException(401, "Sessiya bitib. Yenidən daxil olun.")
    # Sürüşən müddət: aktiv istifadəçinin sessiyası uzadılır.
    if (t - s.last_seen) > timedelta(minutes=5):
        s.last_seen = t
        s.expires_at = t + timedelta(hours=settings.session_hours)
        db.commit()
    request.state.user = user
    return user


def require_admin(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(403, "Bu əməliyyat üçün icazəniz yoxdur.")
    return user


def require_jury(user: User = Depends(current_user)) -> User:
    if user.role != "jury":
        raise HTTPException(403, "Bu bölmə yalnız jüri üçündür.")
    return user


# ---------------------------------------------------------------- giriş limiti
USER_MAX_FAILS, IP_MAX_FAILS = 5, 30
WINDOW = timedelta(minutes=15)
LOCK = timedelta(minutes=15)


def _limit_for(key: str) -> int:
    return USER_MAX_FAILS if key.startswith("u:") else IP_MAX_FAILS


def check_throttle(db: Session, keys: list[str]) -> None:
    t = now()
    rows = db.scalars(select(LoginThrottle).where(LoginThrottle.key.in_(keys))).all()
    for r in rows:
        if r.locked_until and r.locked_until > t:
            minutes = max(1, int((r.locked_until - t).total_seconds() // 60) + 1)
            raise HTTPException(
                429, f"Çoxsaylı uğursuz giriş cəhdi. {minutes} dəqiqə sonra yenidən cəhd edin."
            )


def register_failure(db: Session, keys: list[str]) -> None:
    t = now()
    for key in keys:
        db.execute(
            pg_insert(LoginThrottle)
            .values(key=key, failures=0, window_start=t)
            .on_conflict_do_nothing(index_elements=["key"])
        )
        r = db.execute(select(LoginThrottle).where(LoginThrottle.key == key).with_for_update()).scalar_one()
        if t - r.window_start > WINDOW:
            r.failures, r.window_start, r.locked_until = 0, t, None
        r.failures += 1
        if r.failures >= _limit_for(key):
            r.locked_until = t + LOCK
            r.failures, r.window_start = 0, t


def reset_throttle(db: Session, key: str) -> None:
    r = db.get(LoginThrottle, key)
    if r:
        db.delete(r)


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


# ---------------------------------------------------------------- operator icazələri
# Admin hər operatora bu icazələrdən istədiyini verir. Admin hamısına malikdir.
PERMISSIONS = {
    "contests": "Müsabiqə yaratmaq və ayarlamaq",
    "juries": "Jüri əlavə etmək",
    "teams": "Komandaları müəyyənləşdirmək",
    "criteria": "Meyarları müəyyənləşdirmək",
}
NO_PERM = "Bu əməliyyat üçün icazəniz yoxdur. Adminə müraciət edin."


def user_perms(user: User) -> list[str]:
    if user.role == "admin":
        return list(PERMISSIONS)
    if user.role == "operator":
        return [p for p in (user.permissions or []) if p in PERMISSIONS]
    return []


def require_staff(user: User = Depends(current_user)) -> User:
    """Admin və ya operator."""
    if user.role not in ("admin", "operator"):
        raise HTTPException(403, "Bu əməliyyat üçün icazəniz yoxdur.")
    return user


def require_perm(perm: str):
    assert perm in PERMISSIONS

    def dep(user: User = Depends(require_staff)) -> User:
        if user.role != "admin" and perm not in user_perms(user):
            raise HTTPException(403, NO_PERM)
        return user

    dep.__name__ = f"require_perm_{perm}"
    return dep
