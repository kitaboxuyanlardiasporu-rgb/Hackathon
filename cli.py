"""Sayt sahibi üçün admin idarəetmə əmrləri (yalnız serverdə icra olunur).

İstifadə:
    python -m app.cli create-admin --username admin
    python -m app.cli reset-admin-password --username admin
    echo "parol" | python -m app.cli create-admin --username admin --password-stdin
"""

import argparse
import getpass
import sys

from fastapi import HTTPException
from sqlalchemy import func, select

from .db import SessionLocal
from .models import SessionToken, User
from .security import hash_password, validate_password
from .setup_db import init_db


def _ask_password(from_stdin: bool = False) -> str:
    if from_stdin:
        pw = sys.stdin.readline().rstrip("\r\n")
        try:
            validate_password(pw)
        except HTTPException as e:
            print(e.detail)
            sys.exit(1)
        return pw
    while True:
        p1 = getpass.getpass("Parol (ən azı 8 simvol): ")
        p2 = getpass.getpass("Parolu təkrarlayın: ")
        if p1 != p2:
            print("Parollar uyğun gəlmir.")
            continue
        try:
            validate_password(p1)
        except HTTPException as e:
            print(e.detail)
            continue
        return p1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m app.cli")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create-admin", help="Admin hesabı yaradır")
    c.add_argument("--username", required=True)
    c.add_argument("--password-stdin", action="store_true", help="Parolu standart girişdən oxu")
    r = sub.add_parser("reset-admin-password", help="Admin parolunu yeniləyir")
    r.add_argument("--username", required=True)
    r.add_argument("--password-stdin", action="store_true", help="Parolu standart girişdən oxu")
    args = ap.parse_args(argv)

    init_db()
    with SessionLocal() as db:
        u = db.scalar(select(User).where(func.lower(User.username) == args.username.lower()))
        if args.cmd == "create-admin":
            if u:
                print("Bu istifadəçi adı artıq mövcuddur.")
                return 1
            pw = _ask_password(args.password_stdin)
            db.add(User(username=args.username.strip(), password_hash=hash_password(pw), role="admin"))
            db.commit()
            print("Admin hesabı yaradıldı.")
        else:
            if not u or u.role != "admin":
                print("Admin tapılmadı.")
                return 1
            u.password_hash = hash_password(_ask_password(args.password_stdin))
            u.version += 1
            db.query(SessionToken).filter(SessionToken.user_id == u.id).delete()
            db.commit()
            print("Parol yeniləndi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
