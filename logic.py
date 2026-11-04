from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import AuditLog, Contest, Criterion, Evaluation, Score, Team, User

TYPE_LABELS = {
    "unique": "Unikal bal",
    "scale5": "Şkala",
    "custom": "Fərdi şkala",
}


def lock_contest(db: Session, contest_id: int) -> Contest:
    """Müsabiqə daxilində bütün struktur və bal yazma əməliyyatlarını ardıcıllaşdıran kilid."""
    c = db.execute(select(Contest).where(Contest.id == contest_id).with_for_update()).scalar_one_or_none()
    if c is None:
        raise HTTPException(404, "Müsabiqə tapılmadı. Silinmiş ola bilər; səhifəni yeniləyin.")
    return c


def get_contest(db: Session, contest_id: int) -> Contest:
    c = db.get(Contest, contest_id)
    if c is None:
        raise HTTPException(404, "Müsabiqə tapılmadı. Silinmiş ola bilər; səhifəni yeniləyin.")
    return c


def team_count(db: Session, contest_id: int) -> int:
    return db.scalar(select(func.count(Team.id)).where(Team.contest_id == contest_id)) or 0


def jury_count(db: Session, contest_id: int) -> int:
    return db.scalar(
        select(func.count(User.id)).where(User.role == "jury", User.contest_id == contest_id)
    ) or 0


def score_max(contest: Contest, n_teams: int) -> int:
    if contest.eval_type == "unique":
        return n_teams
    if contest.eval_type == "scale5":
        return 5
    return contest.custom_max or 10


def type_info(contest: Contest, n_teams: int) -> dict:
    mx = score_max(contest, n_teams)
    rng = f"1–{mx}" if mx >= 1 else "—"
    repeat = contest.eval_type != "unique"
    label = TYPE_LABELS[contest.eval_type]
    return {
        "eval_type": contest.eval_type,
        "type_label": label,
        "min": 1,
        "max": mx,
        "range_label": rng,
        "repeats_allowed": repeat,
        "summary": f"{label} — {rng}, {'təkrara icazə verilir' if repeat else 'təkrarsız'}",
    }


def contest_payload(db: Session, contest: Contest) -> dict:
    n = team_count(db, contest.id)
    creator = db.get(User, contest.created_by) if contest.created_by else None
    return {
        "id": contest.id,
        "name": contest.name,
        "created_by": contest.created_by,
        "created_by_username": creator.username if creator else None,
        "created_by_role": creator.role if creator else None,
        "is_open": contest.is_open,
        "custom_max": contest.custom_max,
        "structure_locked": contest.structure_locked,
        "locked_at": contest.locked_at.isoformat() if contest.locked_at else None,
        "created_at": contest.created_at.isoformat() if contest.created_at else None,
        "version": contest.version,
        **type_info(contest, n),
    }


def is_valid_score(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def check_range(contest: Contest, n_teams: int, value) -> None:
    mx = score_max(contest, n_teams)
    if not is_valid_score(value):
        raise HTTPException(400, "Bal tam ədəd olmalıdır.")
    if value < 1 or value > mx:
        raise HTTPException(400, f"Bal 1 ilə {mx} arasında tam ədəd olmalıdır.")


def audit(db: Session, actor: User, action: str, summary: str, details: dict | None = None,
          contest_id: int | None = None) -> None:
    db.add(
        AuditLog(
            actor_id=actor.id,
            actor_username=actor.username,
            actor_role=actor.role,
            action=action,
            summary=summary,
            details=details,
            contest_id=contest_id,
        )
    )


# ---------------------------------------------------------------- nəticələr
def progress(db: Session, contest_id: int) -> dict:
    n_teams = team_count(db, contest_id)
    n_juries = jury_count(db, contest_id)
    expected = n_teams * n_juries
    completed = db.scalar(select(func.count(Evaluation.id)).where(Evaluation.contest_id == contest_id)) or 0
    final = n_juries > 0 and n_teams > 0 and completed >= expected
    pct = round(completed * 100 / expected, 1) if expected else 0.0
    return {
        "teams": n_teams,
        "juries": n_juries,
        "expected": expected,
        "completed": completed,
        "percent": pct,
        "final": final,
        "status_label": "Yekun nəticələr" if final else "Cari nəticələr",
    }


def jury_progress(db: Session, contest_id: int) -> list[dict]:
    n_teams = team_count(db, contest_id)
    counts = dict(
        db.execute(
            select(Evaluation.jury_id, func.count(Evaluation.id))
            .where(Evaluation.contest_id == contest_id)
            .group_by(Evaluation.jury_id)
        ).all()
    )
    juries = db.scalars(
        select(User).where(User.role == "jury", User.contest_id == contest_id).order_by(func.lower(User.username))
    ).all()
    return [
        {
            "id": j.id,
            "username": j.username,
            "completed": counts.get(j.id, 0),
            "total": n_teams,
            "version": j.version,
        }
        for j in juries
    ]


def compute_results(db: Session, contest_id: int) -> dict:
    contest = get_contest(db, contest_id)
    teams = db.scalars(select(Team).where(Team.contest_id == contest_id).order_by(Team.position, Team.id)).all()
    criteria = db.scalars(
        select(Criterion).where(Criterion.contest_id == contest_id).order_by(Criterion.position, Criterion.id)
    ).all()
    sums = {
        (t, c): s
        for t, c, s in db.execute(
            select(Score.team_id, Score.criterion_id, func.sum(Score.value))
            .join(Evaluation, Evaluation.id == Score.evaluation_id)
            .where(Evaluation.contest_id == contest_id)
            .group_by(Score.team_id, Score.criterion_id)
        ).all()
    }
    jcount = dict(
        db.execute(
            select(Evaluation.team_id, func.count(Evaluation.id))
            .where(Evaluation.contest_id == contest_id)
            .group_by(Evaluation.team_id)
        ).all()
    )
    rows = []
    for t in teams:
        per = [int(sums.get((t.id, c.id), 0)) for c in criteria]
        rows.append(
            {
                "team_id": t.id,
                "team": t.name,
                "position": t.position,
                "criteria": per,
                "juries": jcount.get(t.id, 0),
                "total": sum(per),
                "rank": None,
            }
        )
    evaluated = [r for r in rows if r["juries"] > 0]
    evaluated.sort(key=lambda r: (-r["total"], r["position"], r["team_id"]))
    # Standart yarış sıralaması: 1, 2, 2, 4
    for r in evaluated:
        r["rank"] = 1 + sum(1 for o in evaluated if o["total"] > r["total"])
    unevaluated = [r for r in rows if r["juries"] == 0]
    ordered = evaluated + unevaluated
    for r in ordered:
        r.pop("position", None)
    return {
        "contest": contest_payload(db, contest),
        "criteria": [{"id": c.id, "name": c.name} for c in criteria],
        "rows": ordered,
        "progress": progress(db, contest_id),
    }
