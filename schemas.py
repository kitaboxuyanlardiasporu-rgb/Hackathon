from typing import Literal

from pydantic import BaseModel, Field, StrictInt


class LoginIn(BaseModel):
    username: str = Field(max_length=100)
    password: str = Field(max_length=200)


class PasswordChangeIn(BaseModel):
    current_password: str = Field(max_length=200)
    new_password: str = Field(max_length=200)


class ContestUpdateIn(BaseModel):
    name: str
    eval_type: Literal["unique", "scale5", "custom"]
    custom_max: StrictInt | None = None
    version: StrictInt


class NameIn(BaseModel):
    name: str


class RenameIn(BaseModel):
    name: str
    version: StrictInt


class JuryCreateIn(BaseModel):
    username: str
    password: str


class JuryRenameIn(BaseModel):
    username: str
    version: StrictInt


class JuryPasswordIn(BaseModel):
    password: str


class ScoreIn(BaseModel):
    criterion_id: StrictInt
    value: StrictInt


class ConfirmIn(BaseModel):
    team_id: StrictInt
    scores: list[ScoreIn]


class EvalChangeIn(BaseModel):
    evaluation_id: StrictInt
    version: StrictInt
    scores: list[ScoreIn]


class EvalEditIn(BaseModel):
    changes: list[EvalChangeIn]


class UnlockIn(BaseModel):
    version: StrictInt


class ContestCreateIn(BaseModel):
    name: str
    eval_type: Literal["unique", "scale5", "custom"] = "unique"
    custom_max: StrictInt | None = None
    seed_defaults: bool = True
    team_count: StrictInt = 10


class ContestStatusIn(BaseModel):
    is_open: bool


class ContestDeleteIn(BaseModel):
    confirm_name: str
