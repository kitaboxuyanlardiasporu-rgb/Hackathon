from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .logic import audit
from .models import SessionToken, User
from .schemas import LoginIn, PasswordChangeIn
from .security import (
    DUMMY_HASH,
    check_throttle,
    clear_session_cookie,
    client_ip,
    create_session,
    current_user,
    delete_session,
    hash_password,
    register_failure,
    require_admin,
    reset_throttle,
    set_session_cookie,
    validate_password,
    verify_password,
    _token_hash,
)

router = APIRouter(prefix="/api/auth")

BAD_LOGIN = "İstifadəçi adı və ya parol yanlışdır."


def user_payload(u: User) -> dict:
    return {"id": u.id, "username": u.username, "role": u.role, "contest_id": u.contest_id}


@router.post("/login")
def login(body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    uname = body.username.strip()
    if not uname or not body.password:
        raise HTTPException(400, "İstifadəçi adı və parolu daxil edin.")
    keys = [f"u:{uname.lower()}", f"ip:{client_ip(request)}"]
    check_throttle(db, keys)

    user = db.scalar(select(User).where(func.lower(User.username) == uname.lower()))
    ok = verify_password(body.password, user.password_hash if user else DUMMY_HASH)
    if not user or not ok or not user.active:
        register_failure(db, keys)
        db.commit()
        raise HTTPException(401, BAD_LOGIN)

    reset_throttle(db, keys[0])
    old = request.cookies.get(settings.cookie_name)
    delete_session(db, old)
    token = create_session(db, user)
    db.commit()
    set_session_cookie(response, token, request)
    return {"user": user_payload(user)}


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    delete_session(db, request.cookies.get(settings.cookie_name))
    db.commit()
    clear_session_cookie(response, request)
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {"user": user_payload(user)}


@router.post("/password")
def change_own_password(
    body: PasswordChangeIn,
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(400, "Cari parol yanlışdır.")
    validate_password(body.new_password)
    user.password_hash = hash_password(body.new_password)
    user.version += 1
    # Digər cihazlardakı sessiyaları bağlayırıq, cari sessiya qalır.
    cur = _token_hash(request.cookies.get(settings.cookie_name, ""))
    db.execute(delete(SessionToken).where(SessionToken.user_id == user.id, SessionToken.token_hash != cur))
    audit(db, user, "admin_password", "Admin öz parolunu dəyişdi.")
    db.commit()
    return {"ok": True}
