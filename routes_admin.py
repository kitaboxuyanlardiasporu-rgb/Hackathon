import csv
import io
import re
from datetime import datetime, timezone
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import delete, func, select
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
from .models import AuditLog, Criterion, Evaluation, Score, SessionToken, Team, User
from .schemas import (
    ContestUpdateIn,
    EvalEditIn,
    JuryCreateIn,
    JuryPasswordIn,
    JuryRenameIn,
    NameIn,
    RenameIn,
    UnlockIn,
)
from .security import hash_password, require_admin, validate_password

router = APIRouter(prefix="/api/admin", dependencies=[Depends(require_admin)])

CONFLICT_MSG = "Bu məlumat başqa istifadəçi tərəfindən dəyişdirilib. Səhifəni yeniləyib yenidən cəhd edin."
USERNAME_RE = re.compile(r"^[\w.\-]{3,50}$", re.UNICODE)


def clean_name(value: str, what: str, max_len: int = 100) -> str:
    v = re.sub(r"\s+", " ", (value or "")).strip()
    if not v:
        raise HTTPException(400, f"{what} boş ola bilməz.")
    if len(v) > max_len:
        raise HTTPException(400, f"{what} ən çoxu {max_len} simvol ola bilər.")
    return v


# ---------------------------------------------------------------- icmal
@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    contest = get_contest(db)
    return {
        "contest": contest_payload(db, contest),
        "criteria_count": db.scalar(select(func.count(Criterion.id))) or 0,
        "progress": progress(db),
        "juries": jury_progress(db),
    }


# ---------------------------------------------------------------- ayarlar
@router.get("/contest")
def get_contest_settings(db: Session = Depends(get_db)):
    return {"contest": contest_payload(db, get_contest(db)), "teams": team_count(db)}


@router.put("/contest")
def update_contest(body: ContestUpdateIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    contest = lock_contest(db)
    if body.version != contest.version:
        raise HTTPException(409, CONFLICT_MSG)
    name = clean_name(body.name, "Müsabiqənin adı", 200)
    new_max = contest.custom_max
    if body.eval_type == "custom":
        if body.custom_max is None or not (2 <= body.custom_max <= 100):
            raise HTTPException(400, "Maksimum bal 2 ilə 100 arasında tam ədəd olmalıdır.")
        new_max = body.custom_max
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
        audit(db, admin, "contest_update", "Müsabiqə ayarları dəyişdirildi.", {"changes": changes})
    db.commit()
    return {"contest": contest_payload(db, contest)}


# ---------------------------------------------------------------- komandalar və meyarlar
def _entity_routes(model, path: str, label: str, label_gen: str, action: str):
    """Komanda və meyar üçün eyni CRUD qaydaları."""

    def _list(db: Session = Depends(get_db)):
        contest = get_contest(db)
        items = db.scalars(select(model).order_by(model.position, model.id)).all()
        return {
            "items": [{"id": i.id, "name": i.name, "version": i.version} for i in items],
            "structure_locked": contest.structure_locked,
            "contest": contest_payload(db, contest),
        }

    def _create(body: NameIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
        contest = lock_contest(db)
        if contest.structure_locked:
            raise HTTPException(409, f"İlk qiymətləndirmə təsdiqləndikdən sonra {label_gen} sayı dəyişdirilə bilməz.")
        name = clean_name(body.name, f"{label} adı")
        if db.scalar(select(model.id).where(func.lower(model.name) == name.lower())):
            raise HTTPException(409, f"Bu adda {label.lower()} artıq mövcuddur.")
        pos = (db.scalar(select(func.max(model.position))) or 0) + 1
        item = model(name=name, position=pos)
        db.add(item)
        db.flush()
        audit(db, admin, f"{action}_create", f"{label} əlavə edildi: «{name}».")
        db.commit()
        return {"id": item.id, "name": item.name, "version": item.version}

    def _rename(item_id: int, body: RenameIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
        lock_contest(db)
        item = db.get(model, item_id)
        if not item:
            raise HTTPException(404, f"{label} tapılmadı.")
        if item.version != body.version:
            raise HTTPException(409, CONFLICT_MSG)
        name = clean_name(body.name, f"{label} adı")
        if db.scalar(select(model.id).where(func.lower(model.name) == name.lower(), model.id != item.id)):
            raise HTTPException(409, f"Bu adda {label.lower()} artıq mövcuddur.")
        if name != item.name:
            audit(db, admin, f"{action}_rename", f"{label} adı dəyişdirildi: «{item.name}» → «{name}».")
            item.name = name
            item.version += 1
        db.commit()
        return {"id": item.id, "name": item.name, "version": item.version}

    def _delete(item_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
        contest = lock_contest(db)
        if contest.structure_locked:
            raise HTTPException(409, f"İlk qiymətləndirmə təsdiqləndikdən sonra {label_gen} silmək mümkün deyil.")
        item = db.get(model, item_id)
        if not item:
            raise HTTPException(404, f"{label} tapılmadı.")
        audit(db, admin, f"{action}_delete", f"{label} silindi: «{item.name}».")
        db.delete(item)
        db.commit()
        return {"ok": True}

    router.add_api_route(f"/{path}", _list, methods=["GET"])
    router.add_api_route(f"/{path}", _create, methods=["POST"])
    router.add_api_route(f"/{path}/{{item_id}}", _rename, methods=["PATCH"])
    router.add_api_route(f"/{path}/{{item_id}}", _delete, methods=["DELETE"])


_entity_routes(Team, "teams", "Komanda", "komanda", "team")
_entity_routes(Criterion, "criteria", "Meyar", "meyar", "criterion")


# ---------------------------------------------------------------- jürilər
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


@router.get("/juries")
def list_juries(db: Session = Depends(get_db)):
    return {"items": jury_progress(db), "progress": progress(db)}


@router.post("/juries")
def create_jury(body: JuryCreateIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    lock_contest(db)
    u = _clean_username(body.username)
    validate_password(body.password)
    if _username_taken(db, u):
        raise HTTPException(409, "Bu istifadəçi adı artıq istifadə olunur.")
    j = User(username=u, password_hash=hash_password(body.password), role="jury")
    db.add(j)
    db.flush()
    audit(db, admin, "jury_create", f"Jüri hesabı yaradıldı: «{u}».")
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Bu istifadəçi adı artıq istifadə olunur.")
    return {"id": j.id, "username": j.username}


def _get_jury(db: Session, jury_id: int) -> User:
    j = db.get(User, jury_id)
    if not j or j.role != "jury":
        raise HTTPException(404, "Jüri tapılmadı.")
    return j


@router.patch("/juries/{jury_id}")
def rename_jury(jury_id: int, body: JuryRenameIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    lock_contest(db)
    j = _get_jury(db, jury_id)
    if j.version != body.version:
        raise HTTPException(409, CONFLICT_MSG)
    u = _clean_username(body.username)
    if _username_taken(db, u, j.id):
        raise HTTPException(409, "Bu istifadəçi adı artıq istifadə olunur.")
    if u != j.username:
        audit(db, admin, "jury_rename", f"Jüri istifadəçi adı dəyişdirildi: «{j.username}» → «{u}».")
        j.username = u
        j.version += 1
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Bu istifadəçi adı artıq istifadə olunur.")
    return {"id": j.id, "username": j.username, "version": j.version}


@router.post("/juries/{jury_id}/password")
def reset_jury_password(
    jury_id: int, body: JuryPasswordIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    j = _get_jury(db, jury_id)
    validate_password(body.password)
    j.password_hash = hash_password(body.password)
    j.version += 1
    db.execute(delete(SessionToken).where(SessionToken.user_id == j.id))
    audit(db, admin, "jury_password", f"«{j.username}» jürisi üçün yeni parol təyin edildi.")
    db.commit()
    return {"ok": True}


@router.delete("/juries/{jury_id}")
def delete_jury(jury_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    lock_contest(db)
    j = _get_jury(db, jury_id)
    if db.scalar(select(func.count(Evaluation.id)).where(Evaluation.jury_id == j.id)):
        raise HTTPException(
            409, "Bu jürinin təsdiqlənmiş qiymətləndirmələri var. Silmək üçün əvvəlcə onların kilidini açın."
        )
    audit(db, admin, "jury_delete", f"Jüri hesabı silindi: «{j.username}».")
    db.delete(j)
    db.commit()
    return {"ok": True}


# ---------------------------------------------------------------- qiymətləndirmələr
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


@router.get("/juries/{jury_id}/evaluations")
def jury_evaluations(jury_id: int, db: Session = Depends(get_db)):
    j = _get_jury(db, jury_id)
    contest = get_contest(db)
    teams = db.scalars(select(Team).order_by(Team.position, Team.id)).all()
    criteria = db.scalars(select(Criterion).order_by(Criterion.position, Criterion.id)).all()
    evals = {
        e.team_id: e
        for e in db.scalars(
            select(Evaluation).where(Evaluation.jury_id == j.id).options(selectinload(Evaluation.scores))
        ).all()
    }
    return {
        "jury": {"id": j.id, "username": j.username},
        "contest": contest_payload(db, contest),
        "criteria": [{"id": c.id, "name": c.name} for c in criteria],
        "teams": [{"id": t.id, "name": t.name, "evaluation": _eval_payload(evals.get(t.id))} for t in teams],
    }


@router.put("/juries/{jury_id}/evaluations")
def edit_evaluations(
    jury_id: int, body: EvalEditIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    contest = lock_contest(db)
    j = _get_jury(db, jury_id)
    if not body.changes:
        raise HTTPException(400, "Dəyişiklik yoxdur.")
    criteria = {c.id: c.name for c in db.scalars(select(Criterion)).all()}
    n = team_count(db)
    evals = {
        e.id: e
        for e in db.scalars(
            select(Evaluation).where(Evaluation.jury_id == j.id).options(selectinload(Evaluation.scores))
        ).all()
    }
    team_names = {t.id: t.name for t in db.scalars(select(Team)).all()}

    # Yekun vəziyyəti qururuq: {evaluation_id: {criterion_id: value}}
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
            db.add(
                Score(
                    evaluation_id=eid, jury_id=j.id, team_id=e.team_id, criterion_id=c, value=v, unique_scope=unique
                )
            )
        e.version += 1
        e.edited_at = t
    audit(
        db,
        admin,
        "scores_edit",
        f"«{j.username}» jürisinin balları redaktə edildi ({len(touched)} komanda).",
        {"jury": j.username, "items": changes_log},
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, CONFLICT_MSG)
    return {"ok": True, "changed": len(touched)}


@router.post("/evaluations/{evaluation_id}/unlock")
def unlock_evaluation(
    evaluation_id: int, body: UnlockIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    lock_contest(db)
    e = db.scalar(
        select(Evaluation).where(Evaluation.id == evaluation_id).options(selectinload(Evaluation.scores))
    )
    if not e:
        raise HTTPException(404, "Qiymətləndirmə tapılmadı. Artıq kilidi açılmış ola bilər.")
    if e.version != body.version:
        raise HTTPException(409, CONFLICT_MSG)
    jury = db.get(User, e.jury_id)
    team = db.get(Team, e.team_id)
    criteria = {c.id: c.name for c in db.scalars(select(Criterion)).all()}
    old = {criteria.get(s.criterion_id, str(s.criterion_id)): s.value for s in e.scores}
    audit(
        db,
        admin,
        "evaluation_unlock",
        f"«{jury.username}» jürisinin «{team.name}» komandası üzrə qiymətləndirməsinin kilidi açıldı, ballar silindi.",
        {"jury": jury.username, "team": team.name, "deleted_scores": old},
    )
    db.delete(e)  # ballar kaskadla silinir; unikal ballar yenidən istifadəyə açılır
    db.commit()
    return {"ok": True}


# ---------------------------------------------------------------- nəticələr
@router.get("/results")
def results(db: Session = Depends(get_db)):
    return compute_results(db)


def _csv_safe(v):
    s = str(v)
    if s and s[0] in "=+-@\t\r":
        return "'" + s
    return s


@router.get("/results.csv")
def results_csv(db: Session = Depends(get_db)):
    r = compute_results(db)
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
    fname = f"neticeler-{stamp}.csv"
    nice = quote(f"nəticələr-{stamp}.csv")
    return Response(
        content=data.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=\"{fname}\"; filename*=UTF-8''{nice}"},
    )


# ---------------------------------------------------------------- tarixçə
@router.get("/audit")
def audit_log(
    db: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    only_admin: bool = Query(False),
):
    q = select(AuditLog)
    cq = select(func.count(AuditLog.id))
    if only_admin:
        q = q.where(AuditLog.actor_role == "admin")
        cq = cq.where(AuditLog.actor_role == "admin")
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
