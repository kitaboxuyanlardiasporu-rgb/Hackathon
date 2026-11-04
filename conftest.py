import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://portal:portal@localhost:5432/portal_test")
os.environ["COOKIE_SECURE"] = "auto"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "Admin12345!"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.setup_db import init_db  # noqa: E402

H = {"X-Requested-With": "qiymetlendirme-portali"}


class Api:
    def __init__(self, client: TestClient):
        self.c = client

    def get(self, path, **kw):
        return self.c.get(path, **kw)

    def post(self, path, json=None):
        return self.c.post(path, json=json, headers=H)

    def put(self, path, json=None):
        return self.c.put(path, json=json, headers=H)

    def patch(self, path, json=None):
        return self.c.patch(path, json=json, headers=H)

    def delete(self, path):
        return self.c.delete(path, headers=H)

    def login(self, username, password):
        return self.post("/api/auth/login", {"username": username, "password": password})


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    init_db()
    yield


def new_client() -> Api:
    return Api(TestClient(app))


@pytest.fixture
def admin():
    a = new_client()
    assert a.login("admin", "Admin12345!").status_code == 200
    return a


@pytest.fixture
def make_jury(admin):
    def _make(name, password="Jury12345!"):
        r = admin.post("/api/admin/juries", {"username": name, "password": password})
        assert r.status_code == 200, r.text
        j = new_client()
        assert j.login(name, password).status_code == 200
        j.id = r.json()["id"]
        return j

    return _make


def state(j):
    r = j.get("/api/jury/state")
    assert r.status_code == 200, r.text
    return r.json()


def confirm(j, team_id, values):
    """values: meyar sırasına uyğun bal siyahısı və ya bütün meyarlara eyni bal."""
    st = state(j)
    crits = [c["id"] for c in st["criteria"]]
    if isinstance(values, int):
        values = [values] * len(crits)
    return j.post(
        "/api/jury/evaluations",
        {"team_id": team_id, "scores": [{"criterion_id": c, "value": v} for c, v in zip(crits, values)]},
    )


def set_type(admin, eval_type, custom_max=None):
    cur = admin.get("/api/admin/contest").json()["contest"]
    return admin.put(
        "/api/admin/contest",
        {"name": cur["name"], "eval_type": eval_type, "custom_max": custom_max, "version": cur["version"]},
    )
