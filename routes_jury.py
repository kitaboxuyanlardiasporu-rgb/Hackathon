from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from .db import get_db
from .logic import audit, check_range, contest_payload, get_contest, lock_contest, team_count
from .models import Criterion, Evaluation, Score, Team, User
from .schemas import ConfirmIn
from .security import require_jury

router = APIRouter(prefix="/api/jury")


def _my_evaluations(db: Session, jury_id: int) -> list[Evaluation]:
    return db.scalars(
        select(Evaluation).where(Evaluation.jury_id == jury_id).options(selectinload(Evaluation.scores))
    ).all()


@router.get("/state")
def state(user: User = Depends(require_jury), db: Session = Depends(get_db)):
    contest = get_contest(db)
    teams = db.scalars(select(Team).order_by(Team.position, Team.id)).all()
    criteria = db.scalars(select(Criterion).order_by(Criterion.position, Criterion.id)).all()
    evals = _my_evaluations(db, user.id)
    return {
        "user": {"id": user.id, "username": user.username},
        "contest": contest_payload(db, contest),
        "teams": [{"id": t.id, "name": t.name} for t in teams],
        "criteria": [{"id": c.id, "name": c.name} for c in criteria],
        # Yalnız bu jürinin öz qiymətləndirmələri qaytarılır.
        "evaluations": [
            {
                "team_id": e.team_id,
                "confirmed_at": e.confirmed_at.isoformat(),
                "scores": {str(s.criterion_id): s.value for s in e.scores},
            }
            for e in evals
        ],
    }


@router.post("/evaluations")
def confirm(body: ConfirmIn, user: User = Depends(require_jury), db: Session = Depends(get_db)):
    contest = lock_contest(db)  # ardıcıllaşdırma: paralel sorğular bir-birini pozmur
    team = db.get(Team, body.team_id)
    if not team:
        raise HTTPException(404, "Komanda tapılmadı. Səhifəni yeniləyin.")
    criteria = db.scalars(select(Criterion)).all()
    crit_ids = {c.id for c in criteria}
    crit_names = {c.id: c.name for c in criteria}
    if not crit_ids:
        raise HTTPException(400, "Meyar yoxdur.")

    given: dict[int, int] = {}
    for s in body.scores:
        if s.criterion_id in given:
            raise HTTPException(400, "Eyni meyar üzrə bir neçə bal göndərilib.")
        given[s.criterion_id] = s.value
    if set(given) != crit_ids:
        raise HTTPException(400, "Bütün meyarlar üzrə bal seçilməlidir.")

    n = team_count(db)
    for v in given.values():
        check_range(contest, n, v)

    existing = db.scalar(
        select(Evaluation)
        .where(Evaluation.jury_id == user.id, Evaluation.team_id == team.id)
        .options(selectinload(Evaluation.scores))
    )
    if existing:
        same = {s.criterion_id: s.value for s in existing.scores} == given
        if same:
            # Təkrar göndərilmiş eyni sorğu: əlavə qeyd yaradılmır.
            return {"status": "already_confirmed", "team_id": team.id}
        raise HTTPException(409, "Bu komanda artıq təsdiqlənib. Təsdiqlənmiş balları dəyişmək mümkün deyil.")

    unique = contest.eval_type == "unique"
    if unique:
        rows = db.execute(
            select(Score.criterion_id, Score.value, Team.name)
            .join(Team, Team.id == Score.team_id)
            .where(Score.jury_id == user.id)
        ).all()
        used = {(c, v): tname for c, v, tname in rows}
        conflicts = [
            f"«{crit_names[c]}» meyarında {v} bal artıq «{used[(c, v)]}» komandasına verilib"
            for c, v in given.items()
            if (c, v) in used
        ]
        if conflicts:
            raise HTTPException(409, "; ".join(conflicts) + ".")

    ev = Evaluation(jury_id=user.id, team_id=team.id, confirmed_at=datetime.now(timezone.utc))
    db.add(ev)
    db.flush()
    for c, v in given.items():
        db.add(
            Score(
                evaluation_id=ev.id,
                jury_id=user.id,
                team_id=team.id,
                criterion_id=c,
                value=v,
                unique_scope=unique,
            )
        )
    if not contest.structure_locked:
        contest.structure_locked = True
        contest.locked_at = datetime.now(timezone.utc)
        contest.version += 1
    audit(
        db,
        user,
        "evaluation_confirm",
        f"«{team.name}» komandasının qiymətləndirməsi təsdiqləndi.",
        {"team_id": team.id, "team": team.name, "scores": {crit_names[c]: v for c, v in given.items()}},
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Məlumat eyni anda dəyişdirilib. Səhifəni yeniləyib yenidən yoxlayın.")
    return {"status": "confirmed", "team_id": team.id}
