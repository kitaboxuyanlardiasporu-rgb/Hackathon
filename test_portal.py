from concurrent.futures import ThreadPoolExecutor

from conftest import confirm, new_client, set_type, state


def teams_of(api):
    return [t["id"] for t in state(api)["teams"]] if hasattr(api, "id") else None


def admin_teams(admin):
    return [t["id"] for t in admin.get("/api/admin/teams").json()["items"]]


def admin_criteria(admin):
    return [c["id"] for c in admin.get("/api/admin/criteria").json()["items"]]


# ============================================================ giriş və rollar
def test_seed_defaults(admin):
    t = admin.get("/api/admin/teams").json()["items"]
    assert [x["name"] for x in t] == [f"Komanda {i:02d}" for i in range(1, 11)]
    c = admin.get("/api/admin/criteria").json()["items"]
    assert [x["name"] for x in c] == ["İnnovativlik", "Təsir", "İcra oluna bilmə", "Dayanıqlılıq", "Təqdimat"]
    assert admin.get("/api/admin/contest").json()["contest"]["eval_type"] == "unique"


def test_login_errors_and_session():
    a = new_client()
    r = a.login("admin", "yanlış-parol")
    assert r.status_code == 401 and "yanlışdır" in r.json()["detail"]
    r = a.login("yoxdur", "whatever123")
    assert r.status_code == 401 and r.json()["detail"] == "İstifadəçi adı və ya parol yanlışdır."
    assert a.get("/api/auth/me").status_code == 401
    assert a.login("ADMIN", "Admin12345!").status_code == 200  # ad registrdən asılı deyil
    me = a.get("/api/auth/me").json()["user"]
    assert me["role"] == "admin"
    # Cookie HttpOnly olmalıdır
    r = a.login("admin", "Admin12345!")
    assert "httponly" in r.headers["set-cookie"].lower()
    a.post("/api/auth/logout")
    assert a.get("/api/auth/me").status_code == 401


def test_login_rate_limit():
    a = new_client()
    for _ in range(5):
        assert a.login("admin", "wrong-pass-1").status_code == 401
    r = a.login("admin", "Admin12345!")  # düzgün parol belə müvəqqəti bloklanır
    assert r.status_code == 429 and "dəqiqə" in r.json()["detail"]


def test_no_self_registration_and_csrf(admin):
    a = new_client()
    # Qeydiyyat endpoint-i yoxdur
    assert a.post("/api/auth/register", {"username": "x", "password": "12345678"}).status_code in (404, 405)
    assert a.post("/api/admin/juries", {"username": "hacker", "password": "12345678"}).status_code == 401
    # Xüsusi başlıqsız dəyişiklik sorğusu rədd edilir
    r = admin.c.post("/api/admin/teams", json={"name": "X"})
    assert r.status_code == 403


def test_jury_cannot_access_admin(admin, make_jury):
    j = make_jury("jury1")
    for path in ["/api/admin/overview", "/api/admin/results", "/api/admin/results.csv", "/api/admin/juries",
                 "/api/admin/audit", f"/api/admin/juries/{j.id}/evaluations"]:
        assert j.get(path).status_code == 403, path
    assert j.post("/api/admin/juries", {"username": "jury9", "password": "12345678"}).status_code == 403
    assert j.post("/api/admin/teams", {"name": "X"}).status_code == 403
    assert admin.get("/api/jury/state").status_code == 403


def test_jury_sees_only_own(admin, make_jury):
    j1, j2 = make_jury("jury1"), make_jury("jury2")
    tid = state(j1)["teams"][0]["id"]
    assert confirm(j1, tid, 3).status_code == 200
    s2 = state(j2)
    assert s2["evaluations"] == []
    assert "rows" not in s2 and "results" not in s2
    assert len(state(j1)["evaluations"]) == 1


def test_password_rules_and_reset(admin, make_jury):
    r = admin.post("/api/admin/juries", {"username": "short", "password": "1234567"})
    assert r.status_code == 400 and "8" in r.json()["detail"]
    j = make_jury("jury1")
    assert "password" not in str(admin.get("/api/admin/juries").json())
    assert admin.post(f"/api/admin/juries/{j.id}/password", {"password": "NewPass123"}).status_code == 200
    assert j.get("/api/jury/state").status_code == 401  # köhnə sessiya bağlandı
    assert j.login("jury1", "Jury12345!").status_code == 401
    assert j.login("jury1", "NewPass123").status_code == 200
    # Unikal istifadəçi adı
    assert admin.post("/api/admin/juries", {"username": "JURY1", "password": "12345678"}).status_code == 409
    v = admin.get("/api/admin/juries").json()["items"][0]["version"]
    assert admin.patch(f"/api/admin/juries/{j.id}", {"username": "jury_bir", "version": v}).status_code == 200
    assert j.get("/api/jury/state").status_code == 200  # ad dəyişəndə sessiya qalır


# ============================================================ unikal bal
def test_unique_rules(admin, make_jury):
    j1, j2 = make_jury("jury1"), make_jury("jury2")
    st = state(j1)
    assert st["contest"]["max"] == 10 and st["contest"]["eval_type"] == "unique"
    t = [x["id"] for x in st["teams"]]
    # Eyni bal fərqli meyarlarda: [5,5,5,5,5] icazəlidir
    assert confirm(j1, t[0], 5).status_code == 200
    # Eyni jüri eyni meyarda 5-i ikinci komandaya verə bilmir
    r = confirm(j1, t[1], [5, 1, 1, 1, 1])
    assert r.status_code == 409 and "artıq" in r.json()["detail"]
    # Fərqli jüri eyni balı istifadə edə bilir
    assert confirm(j2, t[0], 5).status_code == 200
    assert confirm(j2, t[1], [4, 6, 6, 6, 6]).status_code == 200
    # Aralıqdan kənar və 0
    assert confirm(j1, t[1], 11).status_code == 400
    assert confirm(j1, t[1], 0).status_code == 400
    # Tam bölgü: jüri 1 bütün komandalara 1..10
    for i, tid in enumerate(t[1:], start=1):
        v = [x for x in range(1, 11) if x != 5][i - 1]
        assert confirm(j1, tid, v).status_code == 200
    vals = sorted(e["scores"][str(state(j1)["criteria"][0]["id"])] for e in state(j1)["evaluations"])
    assert vals == list(range(1, 11))


def test_unique_range_follows_team_count(admin):
    assert admin.post("/api/admin/teams", {"name": "Komanda 11"}).status_code == 200
    assert admin.get("/api/admin/contest").json()["contest"]["max"] == 11
    tid = admin_teams(admin)[0]
    assert admin.delete(f"/api/admin/teams/{tid}").status_code == 200
    admin.delete(f"/api/admin/teams/{admin_teams(admin)[0]}")
    assert admin.get("/api/admin/contest").json()["contest"]["range_label"] == "1–9"


def test_non_integer_scores_rejected(admin, make_jury):
    j = make_jury("jury1")
    st = state(j)
    crits = [c["id"] for c in st["criteria"]]
    for bad in [2.5, "3", True, None]:
        r = j.post("/api/jury/evaluations", {"team_id": st["teams"][0]["id"],
                                              "scores": [{"criterion_id": c, "value": bad} for c in crits]})
        assert r.status_code in (400, 422), bad


# ============================================================ şkala tipləri
def test_scale5(admin, make_jury):
    assert set_type(admin, "scale5").status_code == 200
    admin.post("/api/admin/teams", {"name": "Komanda 11"})
    j = make_jury("jury1")
    st = state(j)
    assert st["contest"]["max"] == 5  # komanda sayından asılı deyil
    t = [x["id"] for x in st["teams"]]
    assert confirm(j, t[0], 4).status_code == 200
    assert confirm(j, t[1], 4).status_code == 200  # təkrar icazəlidir
    assert confirm(j, t[2], 6).status_code == 400
    assert confirm(j, t[2], 0).status_code == 400
    assert confirm(j, t[2], [1, 2, 3, 4, 5]).status_code == 200


def test_custom_scale(admin, make_jury):
    for bad in [1, 101, 0]:
        assert set_type(admin, "custom", bad).status_code == 400
    assert set_type(admin, "custom", None).status_code == 400
    r = admin.put("/api/admin/contest", {"name": "X", "eval_type": "custom", "custom_max": 7.5,
                                          "version": admin.get("/api/admin/contest").json()["contest"]["version"]})
    assert r.status_code == 422
    assert set_type(admin, "custom", 20).status_code == 200
    j = make_jury("jury1")
    st = state(j)
    assert st["contest"]["max"] == 20 and st["contest"]["range_label"] == "1–20"
    t = [x["id"] for x in st["teams"]]
    assert confirm(j, t[0], 20).status_code == 200
    assert confirm(j, t[1], 20).status_code == 200
    assert confirm(j, t[2], 21).status_code == 400


# ============================================================ ümumi davranış
def test_incomplete_and_locked(admin, make_jury):
    j = make_jury("jury1")
    st = state(j)
    t, c = st["teams"][0]["id"], [x["id"] for x in st["criteria"]]
    r = j.post("/api/jury/evaluations", {"team_id": t, "scores": [{"criterion_id": c[0], "value": 1}]})
    assert r.status_code == 400 and "Bütün meyarlar" in r.json()["detail"]
    assert confirm(j, t, 1).status_code == 200
    # Eyni sorğunun təkrarı əlavə qeyd yaratmır
    r = confirm(j, t, 1)
    assert r.status_code == 200 and r.json()["status"] == "already_confirmed"
    # Fərqli ballarla dəyişmək mümkün deyil
    assert confirm(j, t, 2).status_code == 409
    assert len(state(j)["evaluations"]) == 1


def test_structure_lock_after_first_confirm(admin, make_jury):
    j = make_jury("jury1")
    confirm(j, state(j)["teams"][0]["id"], 1)
    c = admin.get("/api/admin/contest").json()["contest"]
    assert c["structure_locked"] and c["locked_at"]
    assert set_type(admin, "scale5").status_code == 409
    assert admin.post("/api/admin/teams", {"name": "Yeni"}).status_code == 409
    assert admin.delete(f"/api/admin/teams/{admin_teams(admin)[0]}").status_code == 409
    assert admin.post("/api/admin/criteria", {"name": "Yeni"}).status_code == 409
    assert admin.delete(f"/api/admin/criteria/{admin_criteria(admin)[0]}").status_code == 409
    # Adların redaktəsi mümkündür
    item = admin.get("/api/admin/teams").json()["items"][0]
    assert admin.patch(f"/api/admin/teams/{item['id']}", {"name": "Alfa", "version": item["version"]}).status_code == 200
    crit = admin.get("/api/admin/criteria").json()["items"][0]
    assert admin.patch(f"/api/admin/criteria/{crit['id']}", {"name": "Yenilikçilik", "version": crit["version"]}).status_code == 200
    # Ad dəyişsə də, ad saxlanılır
    r = admin.put("/api/admin/contest", {"name": "Hakaton 2026", "eval_type": "unique", "custom_max": None,
                                          "version": c["version"]})
    assert r.status_code == 200
    # Kilid açılması strukturu açmır
    ev = admin.get(f"/api/admin/juries/{j.id}/evaluations").json()["teams"][0]["evaluation"]
    assert admin.post(f"/api/admin/evaluations/{ev['id']}/unlock", {"version": ev["version"]}).status_code == 200
    assert admin.get("/api/admin/contest").json()["contest"]["structure_locked"] is True
    assert admin.post("/api/admin/teams", {"name": "Yeni"}).status_code == 409


def test_admin_edit_unique_rules(admin, make_jury):
    j = make_jury("jury1")
    t = [x["id"] for x in state(j)["teams"]]
    confirm(j, t[0], 1)
    confirm(j, t[1], 2)
    data = admin.get(f"/api/admin/juries/{j.id}/evaluations").json()
    crits = [c["id"] for c in data["criteria"]]
    e0, e1 = data["teams"][0]["evaluation"], data["teams"][1]["evaluation"]

    def ch(e, vals):
        return {"evaluation_id": e["id"], "version": e["version"],
                "scores": [{"criterion_id": c, "value": v} for c, v in zip(crits, vals)]}

    # Təkrar bal qəbul edilmir
    r = admin.put(f"/api/admin/juries/{j.id}/evaluations", {"changes": [ch(e0, [2, 1, 1, 1, 1])]})
    assert r.status_code == 409 and "Unikal" in r.json()["detail"]
    # Aralıqdan kənar
    assert admin.put(f"/api/admin/juries/{j.id}/evaluations", {"changes": [ch(e0, [11, 1, 1, 1, 1])]}).status_code == 400
    # Dəyişdirmə (swap) bir əməliyyatda mümkündür
    r = admin.put(f"/api/admin/juries/{j.id}/evaluations",
                  {"changes": [ch(e0, [2, 1, 1, 1, 1]), ch(e1, [1, 2, 2, 2, 2])]})
    assert r.status_code == 200 and r.json()["changed"] == 2
    # Köhnə versiya ilə yazmaq -> konflikt
    r = admin.put(f"/api/admin/juries/{j.id}/evaluations", {"changes": [ch(e0, [3, 1, 1, 1, 1])]})
    assert r.status_code == 409 and "başqa istifadəçi" in r.json()["detail"]
    # Tarixçədə köhnə və yeni ballar
    log = admin.get("/api/admin/audit").json()["items"]
    edit = next(x for x in log if x["action"] == "scores_edit")
    first = edit["details"]["items"][0]["changes"][0]
    assert first["old"] == 1 and first["new"] == 2
    assert edit["actor"] == "admin"


def test_admin_edit_scale_allows_repeats(admin, make_jury):
    set_type(admin, "scale5")
    j = make_jury("jury1")
    t = [x["id"] for x in state(j)["teams"]]
    confirm(j, t[0], 1)
    confirm(j, t[1], 2)
    data = admin.get(f"/api/admin/juries/{j.id}/evaluations").json()
    crits = [c["id"] for c in data["criteria"]]
    e0 = data["teams"][0]["evaluation"]
    body = {"changes": [{"evaluation_id": e0["id"], "version": e0["version"],
                         "scores": [{"criterion_id": c, "value": 2} for c in crits]}]}
    assert admin.put(f"/api/admin/juries/{j.id}/evaluations", body).status_code == 200
    body["changes"][0]["version"] += 1
    body["changes"][0]["scores"][0]["value"] = 6
    assert admin.put(f"/api/admin/juries/{j.id}/evaluations", body).status_code == 400


def test_unlock_frees_unique_scores(admin, make_jury):
    j = make_jury("jury1")
    t = [x["id"] for x in state(j)["teams"]]
    confirm(j, t[0], 7)
    assert confirm(j, t[1], 7).status_code == 409
    ev = admin.get(f"/api/admin/juries/{j.id}/evaluations").json()["teams"][0]["evaluation"]
    assert admin.post(f"/api/admin/evaluations/{ev['id']}/unlock", {"version": ev["version"] + 5}).status_code == 409
    assert admin.post(f"/api/admin/evaluations/{ev['id']}/unlock", {"version": ev["version"]}).status_code == 200
    assert state(j)["evaluations"] == []
    assert confirm(j, t[1], 7).status_code == 200  # bal yenidən istifadəyə açıldı
    assert confirm(j, t[0], 3).status_code == 200  # komanda yenidən qiymətləndirilir
    log = admin.get("/api/admin/audit").json()["items"]
    un = next(x for x in log if x["action"] == "evaluation_unlock")
    assert un["details"]["deleted_scores"]["İnnovativlik"] == 7


def _results(admin):
    r = admin.get("/api/admin/results").json()
    return {row["team"]: row for row in r["rows"]}, r


def test_results_sum_and_ties(admin, make_jury):
    for etype, mx in [("unique", None), ("scale5", None), ("custom", 10)]:
        # hər tip üçün təmiz baza
        from app.db import Base, engine
        from app.setup_db import init_db
        Base.metadata.drop_all(engine); init_db()
        a = new_client(); a.login("admin", "Admin12345!")
        set_type(a, etype, mx)
        a.post("/api/admin/juries", {"username": "jr1", "password": "12345678"})
        a.post("/api/admin/juries", {"username": "jr2", "password": "12345678"})
        j1, j2 = new_client(), new_client()
        j1.login("jr1", "12345678"); j2.login("jr2", "12345678")
        t = [x["id"] for x in state(j1)["teams"]]
        # j1: T1=5x5, T2=4x5, T3=3x5 ; j2: T1=3x5, T2=4x5, T3=5x5 -> T1=40, T2=40, T3=40? fərqləndirək:
        confirm(j1, t[0], [5, 5, 5, 5, 5]); confirm(j2, t[0], [4, 4, 4, 4, 4])   # 45
        confirm(j1, t[1], [4, 4, 4, 4, 4]); confirm(j2, t[1], [5, 5, 5, 5, 5])   # 45
        confirm(j1, t[2], [3, 3, 3, 3, 2]); confirm(j2, t[2], [3, 3, 3, 3, 3])   # 29
        confirm(j1, t[3], [2, 2, 2, 2, 3])                                       # 11 (1 jüri)
        rows, r = _results(a)
        assert rows["Komanda 01"]["total"] == 45 and rows["Komanda 01"]["rank"] == 1
        assert rows["Komanda 02"]["total"] == 45 and rows["Komanda 02"]["rank"] == 1
        assert rows["Komanda 03"]["rank"] == 3 and rows["Komanda 03"]["total"] == 29
        assert rows["Komanda 04"]["rank"] == 4 and rows["Komanda 04"]["juries"] == 1
        assert rows["Komanda 01"]["criteria"] == [9, 9, 9, 9, 9]
        assert rows["Komanda 05"]["rank"] is None and rows["Komanda 05"]["total"] == 0
        assert r["progress"]["final"] is False and r["progress"]["status_label"] == "Cari nəticələr"
        assert r["progress"]["expected"] == 20 and r["progress"]["completed"] == 7
        assert [x["team"] for x in r["rows"]][:4] == ["Komanda 01", "Komanda 02", "Komanda 03", "Komanda 04"]


def test_final_status_and_new_jury(admin, make_jury):
    # 2 komanda ilə sadə ssenari
    ids = admin_teams(admin)
    for tid in ids[2:]:
        assert admin.delete(f"/api/admin/teams/{tid}").status_code == 200
    r = admin.get("/api/admin/results").json()
    assert r["progress"]["final"] is False  # jüri yoxdur -> yekun deyil
    j = make_jury("jury1")
    t = [x["id"] for x in state(j)["teams"]]
    confirm(j, t[0], 1); confirm(j, t[1], 2)
    r = admin.get("/api/admin/results").json()
    assert r["progress"]["final"] is True and r["progress"]["status_label"] == "Yekun nəticələr"
    ov = admin.get("/api/admin/overview").json()
    assert ov["progress"]["percent"] == 100.0 and ov["juries"][0]["completed"] == 2
    make_jury("jury2")
    r = admin.get("/api/admin/results").json()
    assert r["progress"]["final"] is False and r["progress"]["expected"] == 4


def test_csv_export(admin, make_jury):
    j = make_jury("jury1")
    confirm(j, state(j)["teams"][0]["id"], 3)
    item = admin.get("/api/admin/teams").json()["items"][0]
    admin.patch(f"/api/admin/teams/{item['id']}", {"name": "Şəki Əğrəb Çöl", "version": item["version"]})
    r = admin.get("/api/admin/results.csv")
    assert r.status_code == 200
    raw = r.content
    assert raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    assert "Şəki Əğrəb Çöl" in text and "İnnovativlik" in text and "Cari nəticələr" in text
    assert "Yer;Komanda;" in text


def test_concurrent_unique_confirms(admin, make_jury):
    """Eyni jüri eyni balı iki komandaya eyni anda göndərir: yalnız biri qəbul olunmalıdır."""
    j = make_jury("jury1")
    st = state(j)
    crits = [c["id"] for c in st["criteria"]]
    teams = [t["id"] for t in st["teams"]]
    clients = [new_client() for _ in teams]
    for c in clients:
        c.login("jury1", "Jury12345!")

    def send(i):
        return clients[i].post("/api/jury/evaluations", {
            "team_id": teams[i], "scores": [{"criterion_id": c, "value": 4} for c in crits]})

    with ThreadPoolExecutor(max_workers=10) as ex:
        codes = sorted(r.status_code for r in ex.map(send, range(len(teams))))
    assert codes.count(200) == 1 and codes.count(409) == len(teams) - 1
    assert len(state(j)["evaluations"]) == 1


def test_concurrent_duplicate_same_team(admin, make_jury):
    j = make_jury("jury1")
    st = state(j)
    crits = [c["id"] for c in st["criteria"]]
    t = st["teams"][0]["id"]
    clients = [new_client() for _ in range(8)]
    for c in clients:
        c.login("jury1", "Jury12345!")
    body = {"team_id": t, "scores": [{"criterion_id": c, "value": 2} for c in crits]}
    with ThreadPoolExecutor(max_workers=8) as ex:
        codes = list(ex.map(lambda c: c.post("/api/jury/evaluations", body).status_code, clients))
    assert all(code == 200 for code in codes)
    assert len(state(j)["evaluations"]) == 1
    ov = admin.get("/api/admin/overview").json()
    assert ov["progress"]["completed"] == 1


def test_concurrent_structure_change_vs_confirm(admin, make_jury):
    """Admin komanda əlavə edərkən jüri təsdiqləyir: nəticə ardıcıl olmalıdır."""
    j = make_jury("jury1")
    t = state(j)["teams"][0]["id"]
    with ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(lambda: confirm(j, t, 1).status_code)
        f2 = ex.submit(lambda: admin.post("/api/admin/teams", {"name": "Komanda 11"}).status_code)
        c1, c2 = f1.result(), f2.result()
    assert c1 == 200
    n = len(admin_teams(admin))
    assert (c2 == 200 and n == 11) or (c2 == 409 and n == 10)


def test_persistence_across_relogin(admin, make_jury):
    j = make_jury("jury1")
    t = state(j)["teams"][0]["id"]
    confirm(j, t, 9)
    j2 = new_client()
    j2.login("jury1", "Jury12345!")  # başqa cihaz
    assert state(j2)["evaluations"][0]["scores"]
    j.post("/api/auth/logout")
    j.login("jury1", "Jury12345!")
    assert len(state(j)["evaluations"]) == 1


def test_delete_jury_rules(admin, make_jury):
    j = make_jury("jury1")
    confirm(j, state(j)["teams"][0]["id"], 1)
    assert admin.delete(f"/api/admin/juries/{j.id}").status_code == 409
    j2 = make_jury("jury2")
    assert admin.delete(f"/api/admin/juries/{j2.id}").status_code == 200


def test_migration_preserves_legacy_data():
    """Köhnə sxem: eval_type sütunu olmayan contest cədvəli 'Unikal bal' kimi qəbul edilir."""
    from sqlalchemy import text
    from app.db import Base, engine
    from app.setup_db import init_db
    Base.metadata.drop_all(engine)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE contest (id INTEGER PRIMARY KEY, name VARCHAR(200) NOT NULL, updated_at TIMESTAMPTZ)"))
        conn.execute(text("INSERT INTO contest (id, name) VALUES (1, 'Köhnə müsabiqə')"))
    init_db()
    a = new_client()
    a.login("admin", "Admin12345!")
    c = a.get("/api/admin/contest").json()["contest"]
    assert c["name"] == "Köhnə müsabiqə" and c["eval_type"] == "unique"


def test_secure_cookie_on_https():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app, base_url="https://testserver")
    r = c.post("/api/auth/login", json={"username": "admin", "password": "Admin12345!"},
               headers={"X-Requested-With": "qiymetlendirme-portali"})
    sc = r.headers["set-cookie"].lower()
    assert r.status_code == 200 and "secure" in sc and "httponly" in sc and "samesite=lax" in sc
