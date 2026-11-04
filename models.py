from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


EVAL_TYPES = ("unique", "scale5", "custom")


class Contest(Base):
    """Müsabiqə. Hər müsabiqənin öz komandaları, meyarları və jüriləri var."""

    __tablename__ = "contest"
    __table_args__ = (
        CheckConstraint("eval_type IN ('unique','scale5','custom')", name="ck_contest_type"),
        CheckConstraint("custom_max IS NULL OR (custom_max BETWEEN 2 AND 100)", name="ck_contest_custom_max"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # Qiymətləndirmə açıqdırsa jürilər bal təsdiqləyə bilər.
    is_open: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, server_default=func.now())
    # Müsabiqəni yaradan istifadəçi (operator yalnız öz müsabiqələrini görür).
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL", use_alter=True, name="contest_created_by_fkey"), nullable=True, index=True
    )
    eval_type: Mapped[str] = mapped_column(String(16), nullable=False, server_default="unique", default="unique")
    custom_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    structure_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"), default=False)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1", default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('admin','operator','jury')", name="ck_users_role"),
        Index("uq_users_username_lower", func.lower(text("username")), unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(10), nullable=False)
    # Operatorun icazələri (məs. ["contests", "juries"]); digər rollar üçün boş.
    permissions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    # Jüri bir müsabiqəyə aiddir; admin və operator üçün boşdur.
    contest_id: Mapped[int | None] = mapped_column(
        ForeignKey("contest.id", ondelete="CASCADE"), nullable=True, index=True
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Team(Base):
    __tablename__ = "teams"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contest_id: Mapped[int] = mapped_column(ForeignKey("contest.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Criterion(Base):
    __tablename__ = "criteria"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contest_id: Mapped[int] = mapped_column(ForeignKey("contest.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Evaluation(Base):
    """Bir jürinin bir komanda üzrə təsdiqlənmiş qiymətləndirməsi."""

    __tablename__ = "evaluations"
    __table_args__ = (UniqueConstraint("jury_id", "team_id", name="uq_eval_jury_team"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contest_id: Mapped[int] = mapped_column(ForeignKey("contest.id", ondelete="CASCADE"), nullable=False, index=True)
    jury_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False, index=True)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    scores: Mapped[list["Score"]] = relationship(
        back_populates="evaluation", cascade="all, delete-orphan", passive_deletes=True
    )


class Score(Base):
    __tablename__ = "scores"
    __table_args__ = (
        UniqueConstraint("evaluation_id", "criterion_id", name="uq_score_eval_criterion"),
        CheckConstraint("value >= 1", name="ck_score_positive"),
        # Unikal bal tipində: eyni jüri, eyni meyar, eyni bal yalnız bir dəfə.
        Index(
            "uq_score_unique_scope",
            "jury_id",
            "criterion_id",
            "value",
            unique=True,
            postgresql_where=text("unique_scope"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    evaluation_id: Mapped[int] = mapped_column(ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False)
    jury_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False)
    criterion_id: Mapped[int] = mapped_column(ForeignKey("criteria.id", ondelete="RESTRICT"), nullable=False)
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    unique_scope: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))

    evaluation: Mapped[Evaluation] = relationship(back_populates="scores")


class SessionToken(Base):
    __tablename__ = "sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LoginThrottle(Base):
    __tablename__ = "login_throttle"
    key: Mapped[str] = mapped_column(String(200), primary_key=True)
    failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    # Müsabiqə silinsə də tarixçə saxlanılır (xarici açar yoxdur).
    contest_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    actor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actor_username: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(10), nullable=False)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
