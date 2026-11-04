import csv
import io
import re
from datetime import datetime, timezone
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from .db import get_db
from .logic import (
    TYPE_LABELS,
    audit,
    check_range,
    compute_results,
    contest_payload,
    get_contest,
    jury_progress,
    lock_contest,
    progress,
    team_count,
)
from .models import AuditLog, Contest, Criterion, Evaluation, Score, SessionToken, Team, User
from .schemas import (
    ContestCreateIn,
    ContestDeleteIn,
    ContestResetIn,
    ContestStatusIn,
    ContestUpdateIn,
    EvalEditIn,
    JuryCreateIn,
    JuryPasswordIn,
    JuryRenameIn,
    NameIn,
    RenameIn,
    OperatorCreateIn,
    OperatorUpdateIn,
    UnlockIn,
)
from .security import PERMISSIONS, hash_password, require_admin, require_perm, require_staff, validate_password
from .setup_db import create_contest

# Admin və operator bu routerə daxil olur; hər endpoint öz icazəsini ayrıca yoxlayır.
def contest_scope(request: Request, user: User = Depends(require_staff), db: Session = Depends(get_db)) -> None:
    """Operator yalnız özünün yaratdığı müsabiqəyə daxil ola bilər (bütün /contests/{cid}/... yolları)."""
    cid = request.path_params.get("cid")
    if cid is None or user.role == "admin":
        return
    c = db.get(Contest, int(cid))
    if c is None or c.created_by != user.id:
        raise HTTPException(404, "Müsabiqə tapılmadı. Silinmiş ola bilər; səhifəni yeniləyin.")


router = APIRouter(prefix="/api/admin", dependencies=[Depends(require_staff), Depends(contest_scope)])
ADMIN_ONLY = [Depends(require_admin)]
PERM_CONTESTS = require_perm("contests")
PERM_JURIES = require_perm("juries")
PERM_OPEN_CLOSE = require_perm("open_close")
PERM_RESET = require_perm("reset")

CONFLICT_MSG = "Bu məlumat başqa istifadəçi tərəfindən dəyişdirilib. Səhifəni yeniləyib yenidən cəhd edin."
USERNAME_RE = re.compile(r"^[\w.\-]{3,50}$", re.UNICODE)
C = "/contests/{cid}"


def clean_name(value: str, what: str, max_len: int = 100) -> str:
    v = re.sub(r"\s+", " ", (value or "")).strip()
    if not v:
        raise HTTPException(400, f"{what} boş ola bilməz.")
    if len(v) > max_len:
        raise HTTPException(400, f"{what} ən çoxu {max_len} simvol ola bilər.")
    return v


def _validate_type(eval_type: str, custom_max) -> int | None:
    if eval_type == "custom":
        if custom_max is None or not (2 <= custom_max <= 100):
            raise HTTPException(400, "Maksimum bal 2 ilə 100 arasında tam ədəd olmalıdır.")
        return custom_max
    return None


def _contest_name_taken(db: Session, name: str, exclude_id: int | None = None) -> bool:
    q = select(Contest.id).where(func.lower(Contest.name) == name.lower())
    if exclude_id:
        q = q.where(Contest.id != exclude_id)
    return db.scalar(q) is not None


# ================================================================ müsabiqələr
@router.get("/contests")
def list_contests(user: User = Depends(require_staff), db: Session = Depends(get_db)):
    q = select(Contest).order_by(Contest.created_at.desc(), Contest.id.desc())
    if user.role != "admin":
        q = q.where(Contest.created_by == user.id)
    contests = db.scalars(q).all()
    return {
        "items": [
            {**contest_payload(db, c), "progress": progress(db, c.id),
             "criteria_count": db.scalar(select(func.count(Criterion.id)).where(Criterion.contest_id == c.id)) or 0}
            for c in contests
        ]
    }


@router.post("/contests")
def create_new_contest(body: ContestCreateIn, admin: User = Depends(PERM_CONTESTS), db: Session = Depends(get_db)):
    name = clean_name(body.name, "Müsabiqənin adı", 200)
    custom_max = _validate_type(body.eval_type, body.custom_max)
    if not (0 <= body.team_count <= 100):
        raise HTTPException(400, "Nümunə komanda sayı 0 ilə 100 arasında olmalıdır.")
    # Eyni adlı iki müsabiqənin eyni anda yaradılmasının qarşısını alırıq.
    db.execute(select(func.pg_advisory_xact_lock(724503)))
    if _contest_name_taken(db, name):
        raise HTTPException(409, "Bu adda müsabiqə artıq mövcuddur.")
    c = create_contest(db, name, body.eval_type, custom_max, seed=body.seed_defaults, created_by=admin.id,
                       teams=body.team_count, is_open=False)
    audit(db, admin, "contest_create", f"Yeni müsabiqə yaradıldı: «{name}».",
          {"type": TYPE_LABELS[body.eval_type]}, contest_id=c.id)
    db.commit()
    return {"contest": contest_payload(db, c)}


@router.post(C + "/status")
def set_contest_status(cid: int, body: ContestStatusIn, admin: User = Depends(PERM_OPEN_CLOSE),
                       db: Session = Depends(get_db)):
    c = lock_contest(db, cid)
    if c.is_open != body.is_open:
        c.is_open = body.is_open
        c.version += 1
        audit(db, admin, "contest_open" if body.is_open else "contest_close",
              f"«{c.name}» üzrə qiymətləndirmə {'açıldı' if body.is_open else 'bağlandı'}.", contest_id=c.id)
    db.commit()
    return {"contest": contest_payload(db, c)}


@router.post(C + "/reset")
def reset_contest(cid: int, body: ContestResetIn, admin: User = Depends(PERM_RESET), db: Session = Depends(get_db)):
    """Bütün ballar silinir; istəyə görə jürilər, komandalar və meyarlar da. Struktur kilidi açılır."""
    c = lock_contest(db, cid)
    if (body.confirm_name or "").strip() != c.name:
        raise HTTPException(400, "Təsdiq üçün müsabiqənin adını dəqiq yazın.")
    before = progress(db, cid)
    criteria = {x.id: x.name for x in _criteria(db, cid)}
    teams = {t.id: t.name for t in _teams(db, cid)}
    juries = {j.id: j.username for j in db.scalars(select(User).where(User.role == "jury", User.contest_id == cid))}
    evals = db.scalars(
        select(Evaluation).where(Evaluation.contest_id == cid).options(selectinload(Evaluation.scores))
    ).all()
    deleted_scores = [
        {"jury": juries.get(e.jury_id, str(e.jury_id)), "team": teams.get(e.team_id, str(e.team_id)),
         "scores": {criteria.get(s.criterion_id, str(s.criterion_id)): s.value for s in e.scores}}
        for e in evals
    ]
    eval_ids = select(Evaluation.id).where(Evaluation.contest_id == cid)
    db.execute(delete(Score).where(Score.evaluation_id.in_(eval_ids)))
    db.execute(delete(Evaluation).where(Evaluation.contest_id == cid))
    removed = []
    if body.juries:
        jids = select(User.id).where(User.role == "jury", User.contest_id == cid)
        db.execute(delete(SessionToken).where(SessionToken.user_id.in_(jids)))
        db.execute(delete(User).where(User.role == "jury", User.contest_id == cid))
        removed.append(f"{len(juries)} jüri")
    if body.teams:
        db.execute(delete(Team).where(Team.contest_id == cid))
        removed.append(f"{len(teams)} komanda")
    if body.criteria:
        db.execute(delete(Criterion).where(Criterion.contest_id == cid))
        removed.append(f"{len(criteria)} meyar")
    c.structure_locked = False
    c.locked_at = None
    c.version += 1
    summary = f"«{c.name}» müsabiqəsinin məlumatları sıfırlandı: {before['completed']} qiymətləndirmə"
    summary += (", " + ", ".join(removed) if removed else "") + " silindi."
    audit(db, admin, "contest_reset", summary,
          {"evaluations": before["completed"], "removed": removed, "deleted_scores": deleted_scores}, contest_id=cid)
    db.commit()
    return {"contest": contest_payload(db, c), "deleted_evaluations": before["completed"]}


@router.post(C + "/delete")
def delete_contest(cid: int, body: ContestDeleteIn, admin: User = Depends(require_admin),
                   db: Session = Depends(get_db)):
    c = lock_contest(db, cid)
    if (body.confirm_name or "").strip() != c.name:
        raise HTTPException(400, "Təsdiq üçün müsabiqənin adını dəqiq yazın.")
    stats = progress(db, cid)
    eval_ids = select(Evaluation.id).where(Evaluation.contest_id == cid)
    db.execute(delete(Score).where(Score.evaluation_id.in_(eval_ids)))
    db.execute(delete(Evaluation).where(Evaluation.contest_id == cid))
    jury_ids = select(User.id).where(User.role == "jury", User.contest_id == cid)
    db.execute(delete(SessionToken).where(SessionToken.user_id.in_(jury_ids)))
    db.execute(delete(User).where(User.role == "jury", User.contest_id == cid))
    db.execute(delete(Team).where(Team.contest_id == cid))
    db.execute(delete(Criterion).where(Criterion.contest_id == cid))
    name = c.name
    db.delete(c)
    audit(db, admin, "contest_delete", f"Müsabiqə həmişəlik silindi: «{name}».",
          {"teams": stats["teams"], "juries": stats["juries"], "evaluations": stats["completed"]})
    db.commit()
    return {"ok": True}


# ================================================================ icmal və ayarlar
@router.get(C + "/overview")
def overview(cid: int, db: Session = Depends(get_db)):
    contest = get_contest(db, cid)
    return {
        "contest": contest_payload(db, contest),
        "criteria_count": db.scalar(select(func.count(Criterion.id)).where(Criterion.contest_id == cid)) or 0,
        "progress": progress(db, cid),
        "juries": jury_progress(db, cid),
    }


@router.get(C + "/contest", dependencies=[Depends(PERM_CONTESTS)])
def get_contest_settings(cid: int, db: Session = Depends(get_db)):
    return {"contest": contest_payload(db, get_contest(db, cid)), "teams": team_count(db, cid)}


@router.put(C + "/contest")
def update_contest(cid: int, body: ContestUpdateIn, admin: User = Depends(PERM_CONTESTS),
                   db: Session = Depends(get_db)):
    contest = lock_contest(db, cid)
    if body.version != contest.version:
        raise HTTPException(409, CONFLICT_MSG)
    name = clean_name(body.name, "Müsabiqənin adı", 200)
    if _contest_name_taken(db, name, contest.id):
        raise HTTPException(409, "Bu adda müsabiqə artıq mövcuddur.")
    new_max = contest.custom_max
    if body.eval_type == "custom":
        new_max = _validate_type("custom", body.custom_max)
    type_changed = body.eval_type != contest.eval_type or (
        body.eval_type == "custom" and new_max != contest.custom_max
    )
    if type_changed and contest.structure_locked:
        raise HTTPException(
            409, "İlk qiymətləndirmə təsdiqləndiyi üçün qiymətləndirmə tipi və şkala həddi dəyişdirilə bilməz."
        )
    changes = {}
    if name != contest.name:
        changes["Ad"] = [contest.name, name]
    if type_changed:
        old = TYPE_LABELS[contest.eval_type] + (f" (1–{contest.custom_max})" if contest.eval_type == "custom" else "")
        new = TYPE_LABELS[body.eval_type] + (f" (1–{new_max})" if body.eval_type == "custom" else "")
        changes["Qiymətləndirmə tipi"] = [old, new]
    contest.name = name
    contest.eval_type = body.eval_type
    contest.custom_max = new_max
    if changes:
        contest.version += 1
        audit(db, admin, "contest_update", "Müsabiqə ayarları dəyişdirildi.", {"changes": changes}, contest_id=cid)
    db.commit()
    return {"contest": contest_payload(db, contest)}


# ================================================================ komandalar və meyarlar
def _entity_routes(model, path: str, label: str, label_gen: str, action: str, perm: str):
    """Komanda və meyar üçün eyni CRUD qaydaları."""
    need = require_perm(perm)

    def _get_item(db: Session, cid: int, item_id: int):
        item = db.get(model, item_id)
        if not item or item.contest_id != cid:
            raise HTTPException(404, f"{label} tapılmadı.")
        return item

    def _taken(db, cid, name, exclude=None):
        q = select(model.id).where(model.contest_id == cid, func.lower(model.name) == name.lower())
        if exclude:
            q = q.where(model.id != exclude)
        return db.scalar(q) is not None

    def _list(cid: int, db: Session = Depends(get_db)):
        contest = get_contest(db, cid)
        items = db.scalars(select(model).where(model.contest_id == cid).order_by(model.position, model.id)).all()
        return {
            "items": [{"id": i.id, "name": i.name, "version": i.version} for i in items],
            "structure_locked": contest.structure_locked,
            "contest": contest_payload(db, contest),
        }

    def _create(cid: int, body: NameIn, admin: User = Depends(need), db: Session = Depends(get_db)):
        contest = lock_contest(db, cid)
        if contest.structure_locked:
            raise HTTPException(409, f"İlk qiymətləndirmə təsdiqləndikdən sonra {label_gen} sayı dəyişdirilə bilməz.")
        name = clean_name(body.name, f"{label} adı")
        if _taken(db, cid, name):
            raise HTTPException(409, f"Bu adda {label.lower()} artıq mövcuddur.")
        pos = (db.scalar(select(func.max(model.position)).where(model.contest_id == cid)) or 0) + 1
        item = model(contest_id=cid, name=name, position=pos)
        db.add(item)
        db.flush()
        audit(db, admin, f"{action}_create", f"{label} əlavə edildi: «{name}».", contest_id=cid)
        db.commit()
        return {"id": item.id, "name": item.name, "version": item.version}

    def _rename(cid: int, item_id: int, body: RenameIn, admin: User = Depends(need),
                db: Session = Depends(get_db)):
        lock_contest(db, cid)
        item = _get_item(db, cid, item_id)
        if item.version != body.version:
            raise HTTPException(409, CONFLICT_MSG)
        name = clean_name(body.name, f"{label} adı")
        if _taken(db, cid, name, item.id):
            raise HTTPException(409, f"Bu adda {label.lower()} artıq mövcuddur.")
        if name != item.name:
            audit(db, admin, f"{action}_rename", f"{label} adı dəyişdirildi: «{item.name}» → «{name}».", contest_id=cid)
            item.name = name
            item.version += 1
        db.commit()
        return {"id": item.id, "name": item.name, "version": item.version}

    def _delete(cid: int, item_id: int, admin: User = Depends(need), db: Session = Depends(get_db)):
        contest = lock_contest(db, cid)
        if contest.structure_locked:
            raise HTTPException(409, f"İlk qiymətləndirmə təsdiqləndikdən sonra {label_gen} silmək mümkün deyil.")
        item = _get_item(db, cid, item_id)
        audit(db, admin, f"{action}_delete", f"{label} silindi: «{item.name}».", contest_id=cid)
        db.delete(item)
        db.commit()
        return {"ok": True}

    router.add_api_route(f"{C}/{path}", _list, methods=["GET"], dependencies=[Depends(need)])
    router.add_api_route(f"{C}/{path}", _create, methods=["POST"])
    router.add_api_route(f"{C}/{path}/{{item_id}}", _rename, methods=["PATCH"])
    router.add_api_route(f"{C}/{path}/{{item_id}}", _delete, methods=["DELETE"])


_entity_routes(Team, "teams", "Komanda", "komanda", "team", "teams")
_entity_routes(Criterion, "criteria", "Meyar", "meyar", "criterion", "criteria")


# ================================================================ jürilər
def _clean_username(u: str) -> str:
    u = (u or "").strip()
    if not USERNAME_RE.match(u):
        raise HTTPException(
            400, "İstifadəçi adı 3–50 simvol olmalı, yalnız hərf, rəqəm, nöqtə, defis və alt xətt içərməlidir."
        )
    return u


def _username_taken(db: Session, u: str, exclude_id: int | None = None) -> bool:
    q = select(User.id).where(func.lower(User.username) == u.lower())
    if exclude_id:
        q = q.where(User.id != exclude_id)
    return db.scalar(q) is not None


TAKEN_MSG = "Bu istifadəçi adı artıq istifadə olunur (başqa müsabiqədə də ola bilər)."


@router.get(C + "/juries", dependencies=[Depends(PERM_JURIES)])
def list_juries(cid: int, db: Session = Depends(get_db)):
    get_contest(db, cid)
    return {"items": jury_progress(db, cid), "progress": progress(db, cid)}


@router.post(C + "/juries")
def create_jury(cid: int, body: JuryCreateIn, admin: User = Depends(PERM_JURIES), db: Session = Depends(get_db)):
    contest = lock_contest(db, cid)
    u = _clean_username(body.username)
    validate_password(body.password)
    if _username_taken(db, u):
        raise HTTPException(409, TAKEN_MSG)
    j = User(username=u, password_hash=hash_password(body.password), role="jury", contest_id=cid)
    db.add(j)
    db.flush()
    audit(db, admin, "jury_create", f"Jüri hesabı yaradıldı: «{u}» ({contest.name}).", contest_id=cid)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, TAKEN_MSG)
    return {"id": j.id, "username": j.username}


def _get_jury(db: Session, cid: int, jury_id: int) -> User:
    j = db.get(User, jury_id)
    if not j or j.role != "jury" or j.contest_id != cid:
        raise HTTPException(404, "Jüri tapılmadı.")
    return j


@router.patch(C + "/juries/{jury_id}")
def rename_jury(cid: int, jury_id: int, body: JuryRenameIn, admin: User = Depends(PERM_JURIES),
                db: Session = Depends(get_db)):
    lock_contest(db, cid)
    j = _get_jury(db, cid, jury_id)
    if j.version != body.version:
        raise HTTPException(409, CONFLICT_MSG)
    u = _clean_username(body.username)
    if _username_taken(db, u, j.id):
        raise HTTPException(409, TAKEN_MSG)
    if u != j.username:
        audit(db, admin, "jury_rename", f"Jüri istifadəçi adı dəyişdirildi: «{j.username}» → «{u}».", contest_id=cid)
        j.username = u
        j.version += 1
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, TAKEN_MSG)
    return {"id": j.id, "username": j.username, "version": j.version}


@router.post(C + "/juries/{jury_id}/password")
def reset_jury_password(cid: int, jury_id: int, body: JuryPasswordIn, admin: User = Depends(PERM_JURIES),
                        db: Session = Depends(get_db)):
    j = _get_jury(db, cid, jury_id)
    validate_password(body.password)
    j.password_hash = hash_password(body.password)
    j.version += 1
    db.execute(delete(SessionToken).where(SessionToken.user_id == j.id))
    audit(db, admin, "jury_password", f"«{j.username}» jürisi üçün yeni parol təyin edildi.", contest_id=cid)
    db.commit()
    return {"ok": True}


@router.delete(C + "/juries/{jury_id}")
def delete_jury(cid: int, jury_id: int, with_scores: bool = Query(False), admin: User = Depends(PERM_JURIES),
                db: Session = Depends(get_db)):
    lock_contest(db, cid)
    j = _get_jury(db, cid, jury_id)
    evals = db.scalars(
        select(Evaluation).where(Evaluation.jury_id == j.id).options(selectinload(Evaluation.scores))
    ).all()
    details = None
    if evals:
        if admin.role != "admin":
            raise HTTPException(403, "Təsdiqlənmiş balı olan jürini yalnız admin silə bilər.")
        if not with_scores:
            raise HTTPException(
                409, "Bu jürinin təsdiqlənmiş qiymətləndirmələri var. Hesabı ballarla birlikdə silmək üçün təsdiq tələb olunur."
            )
        criteria = {c.id: c.name for c in _criteria(db, cid)}
        teams = {t.id: t.name for t in _teams(db, cid)}
        details = {
            "jury": j.username,
            "deleted": {
                teams.get(e.team_id, str(e.team_id)): {criteria.get(s.criterion_id, str(s.criterion_id)): s.value
                                                       for s in e.scores}
                for e in evals
            },
        }
        eval_ids = [e.id for e in evals]
        db.execute(delete(Score).where(Score.evaluation_id.in_(eval_ids)))
        db.execute(delete(Evaluation).where(Evaluation.id.in_(eval_ids)))
    db.execute(delete(SessionToken).where(SessionToken.user_id == j.id))
    summary = f"Jüri hesabı silindi: «{j.username}»."
    if evals:
        summary = f"Jüri hesabı {len(evals)} təsdiqlənmiş qiymətləndirməsi ilə birlikdə silindi: «{j.username}»."
    audit(db, admin, "jury_delete", summary, details, contest_id=cid)
    db.delete(j)
    db.commit()
    return {"ok": True, "deleted_evaluations": len(evals)}


# ================================================================ qiymətləndirmələr
def _eval_payload(e: Evaluation | None):
    if not e:
        return None
    return {
        "id": e.id,
        "version": e.version,
        "confirmed_at": e.confirmed_at.isoformat(),
        "edited_at": e.edited_at.isoformat() if e.edited_at else None,
        "scores": {str(s.criterion_id): s.value for s in e.scores},
    }


def _teams(db, cid):
    return db.scalars(select(Team).where(Team.contest_id == cid).order_by(Team.position, Team.id)).all()


def _criteria(db, cid):
    return db.scalars(
        select(Criterion).where(Criterion.contest_id == cid).order_by(Criterion.position, Criterion.id)
    ).all()


@router.get(C + "/juries/{jury_id}/evaluations", dependencies=ADMIN_ONLY)
def jury_evaluations(cid: int, jury_id: int, db: Session = Depends(get_db)):
    j = _get_jury(db, cid, jury_id)
    contest = get_contest(db, cid)
    evals = {
        e.team_id: e
        for e in db.scalars(
            select(Evaluation).where(Evaluation.jury_id == j.id).options(selectinload(Evaluation.scores))
        ).all()
    }
    return {
        "jury": {"id": j.id, "username": j.username},
        "contest": contest_payload(db, contest),
        "criteria": [{"id": c.id, "name": c.name} for c in _criteria(db, cid)],
        "teams": [{"id": t.id, "name": t.name, "evaluation": _eval_payload(evals.get(t.id))} for t in _teams(db, cid)],
    }


@router.put(C + "/juries/{jury_id}/evaluations")
def edit_evaluations(cid: int, jury_id: int, body: EvalEditIn, admin: User = Depends(require_admin),
                     db: Session = Depends(get_db)):
    contest = lock_contest(db, cid)
    j = _get_jury(db, cid, jury_id)
    if not body.changes:
        raise HTTPException(400, "Dəyişiklik yoxdur.")
    criteria = {c.id: c.name for c in _criteria(db, cid)}
    n = team_count(db, cid)
    evals = {
        e.id: e
        for e in db.scalars(
            select(Evaluation).where(Evaluation.jury_id == j.id).options(selectinload(Evaluation.scores))
        ).all()
    }
    team_names = {t.id: t.name for t in _teams(db, cid)}

    final = {eid: {s.criterion_id: s.value for s in e.scores} for eid, e in evals.items()}
    touched = []
    for ch in body.changes:
        e = evals.get(ch.evaluation_id)
        if not e:
            raise HTTPException(404, "Qiymətləndirmə tapılmadı. Kilidi açılmış ola bilər; səhifəni yeniləyin.")
        if e.version != ch.version:
            raise HTTPException(409, CONFLICT_MSG)
        new = {}
        for s in ch.scores:
            if s.criterion_id not in criteria:
                raise HTTPException(400, "Naməlum meyar.")
            check_range(contest, n, s.value)
            new[s.criterion_id] = s.value
        if set(new) != set(criteria):
            raise HTTPException(400, "Bütün meyarlar üzrə bal daxil edilməlidir.")
        if new != final[e.id]:
            touched.append(e.id)
        final[e.id] = new

    if contest.eval_type == "unique":
        seen = {}
        for eid, sc in final.items():
            for c, v in sc.items():
                key = (c, v)
                if key in seen:
                    t1 = team_names[evals[seen[key]].team_id]
                    t2 = team_names[evals[eid].team_id]
                    raise HTTPException(
                        409,
                        f"Unikal bal qaydası: «{criteria[c]}» meyarında {v} bal həm «{t1}», həm də «{t2}» "
                        "komandasına verilə bilməz.",
                    )
                seen[key] = eid

    if not touched:
        return {"ok": True, "changed": 0}

    unique = contest.eval_type == "unique"
    changes_log = []
    # Unikal indeksin aralıq vəziyyətdə pozulmaması üçün əvvəlcə silib sonra yazırıq.
    for eid in touched:
        e = evals[eid]
        old = {s.criterion_id: s.value for s in e.scores}
        changes_log.append(
            {
                "team": team_names[e.team_id],
                "changes": [
                    {"criterion": criteria[c], "old": old.get(c), "new": final[eid][c]}
                    for c in criteria
                    if old.get(c) != final[eid][c]
                ],
            }
        )
        db.execute(delete(Score).where(Score.evaluation_id == eid))
    db.flush()
    t = datetime.now(timezone.utc)
    for eid in touched:
        e = evals[eid]
        for c, v in final[eid].items():
            db.add(Score(evaluation_id=eid, jury_id=j.id, team_id=e.team_id, criterion_id=c, value=v,
                         unique_scope=unique))
        e.version += 1
        e.edited_at = t
    audit(db, admin, "scores_edit", f"«{j.username}» jürisinin balları redaktə edildi ({len(touched)} komanda).",
          {"jury": j.username, "items": changes_log}, contest_id=cid)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, CONFLICT_MSG)
    return {"ok": True, "changed": len(touched)}


@router.post(C + "/evaluations/{evaluation_id}/unlock")
def unlock_evaluation(cid: int, evaluation_id: int, body: UnlockIn, admin: User = Depends(require_admin),
                      db: Session = Depends(get_db)):
    lock_contest(db, cid)
    e = db.scalar(
        select(Evaluation).where(Evaluation.id == evaluation_id, Evaluation.contest_id == cid)
        .options(selectinload(Evaluation.scores))
    )
    if not e:
        raise HTTPException(404, "Qiymətləndirmə tapılmadı. Artıq kilidi açılmış ola bilər.")
    if e.version != body.version:
        raise HTTPException(409, CONFLICT_MSG)
    jury = db.get(User, e.jury_id)
    team = db.get(Team, e.team_id)
    criteria = {c.id: c.name for c in _criteria(db, cid)}
    old = {criteria.get(s.criterion_id, str(s.criterion_id)): s.value for s in e.scores}
    audit(
        db,
        admin,
        "evaluation_unlock",
        f"«{jury.username}» jürisinin «{team.name}» komandası üzrə qiymətləndirməsinin kilidi açıldı, ballar silindi.",
        {"jury": jury.username, "team": team.name, "deleted_scores": old},
        contest_id=cid,
    )
    db.delete(e)  # ballar kaskadla silinir; unikal ballar yenidən istifadəyə açılır
    db.commit()
    return {"ok": True}


# ================================================================ nəticələr
@router.get(C + "/results", dependencies=ADMIN_ONLY)
def results(cid: int, db: Session = Depends(get_db)):
    return compute_results(db, cid)


def _csv_safe(v):
    s = str(v)
    if s and s[0] in "=+-@\t\r":
        return "'" + s
    return s


@router.get(C + "/results.csv", dependencies=ADMIN_ONLY)
def results_csv(cid: int, db: Session = Depends(get_db)):
    r = compute_results(db, cid)
    c, p = r["contest"], r["progress"]
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";", lineterminator="\r\n")
    w.writerow(["Müsabiqə", _csv_safe(c["name"])])
    w.writerow(["Qiymətləndirmə tipi", c["summary"]])
    w.writerow(["Status", f"{p['status_label']} ({p['completed']}/{p['expected']} qiymətləndirmə)"])
    w.writerow([])
    w.writerow(["Yer", "Komanda", *[_csv_safe(x["name"]) for x in r["criteria"]], "Jüri sayı", "Ümumi bal"])
    for row in r["rows"]:
        w.writerow(
            [row["rank"] if row["rank"] else "—", _csv_safe(row["team"]), *row["criteria"], row["juries"], row["total"]]
        )
    data = "﻿" + buf.getvalue()  # BOM: Excel Azərbaycan hərflərini düzgün açır
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    fname = f"neticeler-{cid}-{stamp}.csv"
    nice = quote(f"nəticələr-{c['name'][:60]}-{stamp}.csv")
    return Response(
        content=data.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=\"{fname}\"; filename*=UTF-8''{nice}"},
    )


# ================================================================ tarixçə
@router.get(C + "/audit", dependencies=ADMIN_ONLY)
def audit_log(
    cid: int,
    db: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    only_admin: bool = Query(False),
):
    # Seçilmiş müsabiqənin qeydləri + ümumi qeydlər (müsabiqə silinməsi, admin parolu və s.)
    cond = or_(AuditLog.contest_id == cid, AuditLog.contest_id.is_(None))
    q = select(AuditLog).where(cond)
    cq = select(func.count(AuditLog.id)).where(cond)
    if only_admin:
        q = q.where(AuditLog.actor_role.in_(("admin", "operator")))
        cq = cq.where(AuditLog.actor_role.in_(("admin", "operator")))
    rows = db.scalars(q.order_by(AuditLog.at.desc(), AuditLog.id.desc()).offset(offset).limit(limit)).all()
    return {
        "total": db.scalar(cq) or 0,
        "items": [
            {
                "id": a.id,
                "at": a.at.isoformat(),
                "actor": a.actor_username,
                "role": a.actor_role,
                "action": a.action,
                "summary": a.summary,
                "details": a.details,
            }
            for a in rows
        ],
    }


# ================================================================ operatorlar (yalnız admin)
def _clean_perms(perms: list[str]) -> list[str]:
    bad = [p for p in perms if p not in PERMISSIONS]
    if bad:
        raise HTTPException(400, "Naməlum icazə.")
    return [p for p in PERMISSIONS if p in perms]  # sabit sıra, təkrarsız


def _perm_labels(perms: list[str]) -> str:
    return ", ".join(PERMISSIONS[p] for p in perms) or "icazə yoxdur"


def _operator_payload(u: User) -> dict:
    return {"id": u.id, "username": u.username, "permissions": _clean_perms(u.permissions or []),
            "version": u.version, "created_at": u.created_at.isoformat() if u.created_at else None}


def _get_operator(db: Session, op_id: int) -> User:
    u = db.get(User, op_id)
    if not u or u.role != "operator":
        raise HTTPException(404, "Operator tapılmadı.")
    return u


@router.get("/operators", dependencies=ADMIN_ONLY)
def list_operators(db: Session = Depends(get_db)):
    ops = db.scalars(select(User).where(User.role == "operator").order_by(func.lower(User.username))).all()
    return {"items": [_operator_payload(u) for u in ops],
            "permissions": [{"key": k, "label": v} for k, v in PERMISSIONS.items()]}


@router.post("/operators")
def create_operator(body: OperatorCreateIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    u = _clean_username(body.username)
    validate_password(body.password)
    perms = _clean_perms(body.permissions)
    if _username_taken(db, u):
        raise HTTPException(409, TAKEN_MSG)
    op = User(username=u, password_hash=hash_password(body.password), role="operator", permissions=perms)
    db.add(op)
    db.flush()
    audit(db, admin, "operator_create", f"Operator hesabı yaradıldı: «{u}».", {"permissions": _perm_labels(perms)})
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, TAKEN_MSG)
    return _operator_payload(op)


@router.patch("/operators/{op_id}")
def update_operator(op_id: int, body: OperatorUpdateIn, admin: User = Depends(require_admin),
                    db: Session = Depends(get_db)):
    op = db.execute(select(User).where(User.id == op_id).with_for_update()).scalar_one_or_none()
    if not op or op.role != "operator":
        raise HTTPException(404, "Operator tapılmadı.")
    if op.version != body.version:
        raise HTTPException(409, CONFLICT_MSG)
    u = _clean_username(body.username)
    perms = _clean_perms(body.permissions)
    if _username_taken(db, u, op.id):
        raise HTTPException(409, TAKEN_MSG)
    changes = {}
    if u != op.username:
        changes["İstifadəçi adı"] = [op.username, u]
    old_perms = _clean_perms(op.permissions or [])
    if perms != old_perms:
        changes["İcazələr"] = [_perm_labels(old_perms), _perm_labels(perms)]
    if changes:
        audit(db, admin, "operator_update", f"Operator dəyişdirildi: «{op.username}».", {"changes": changes})
        op.username = u
        op.permissions = perms
        op.version += 1
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, TAKEN_MSG)
    return _operator_payload(op)


@router.post("/operators/{op_id}/password")
def reset_operator_password(op_id: int, body: JuryPasswordIn, admin: User = Depends(require_admin),
                            db: Session = Depends(get_db)):
    op = _get_operator(db, op_id)
    validate_password(body.password)
    op.password_hash = hash_password(body.password)
    op.version += 1
    db.execute(delete(SessionToken).where(SessionToken.user_id == op.id))
    audit(db, admin, "operator_password", f"«{op.username}» operatoru üçün yeni parol təyin edildi.")
    db.commit()
    return {"ok": True}


@router.delete("/operators/{op_id}")
def delete_operator(op_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    op = _get_operator(db, op_id)
    audit(db, admin, "operator_delete", f"Operator hesabı silindi: «{op.username}».")
    db.execute(delete(SessionToken).where(SessionToken.user_id == op.id))
    db.delete(op)
    db.commit()
    return {"ok": True}
