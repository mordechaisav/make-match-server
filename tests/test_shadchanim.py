def test_register_shadchan_returns_created_record(client):
    resp = client.post(
        "/api/v1/shadchanim",
        json={"name": "R. Cohen", "phone": "050-111-2222", "email": "cohen@shadchanim.example"},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "R. Cohen"
    assert body["phone"] == "050-111-2222"
    assert body["email"] == "cohen@shadchanim.example"
    assert isinstance(body["id"], int)
    assert body["created_at"]
    assert body["updated_at"]


def test_register_shadchan_missing_field_is_422(client):
    resp = client.post("/api/v1/shadchanim", json={"name": "R. Cohen", "phone": "050-111-2222"})

    assert resp.status_code == 422


def test_register_shadchan_same_account_twice_is_409(client):
    body = {"name": "R. Cohen", "phone": "050-111-2222", "email": "cohen@shadchanim.example"}
    first = client.post("/api/v1/shadchanim", json=body)
    assert first.status_code == 201

    second = client.post("/api/v1/shadchanim", json=body)

    assert second.status_code == 409
    detail = second.json()["detail"]
    assert detail["shadchan"]["id"] == first.json()["id"]
    assert detail["shadchan"]["email"] == "cohen@shadchanim.example"


def test_register_shadchan_without_token_is_401(client_no_auth_override):
    resp = client_no_auth_override.post(
        "/api/v1/shadchanim",
        json={"name": "R. Cohen", "phone": "050-111-2222", "email": "cohen@shadchanim.example"},
    )

    assert resp.status_code == 401


def test_get_my_shadchan_returns_own_record(client, shadchan_id):
    resp = client.get("/api/v1/shadchanim/me")

    assert resp.status_code == 200
    assert resp.json()["id"] == shadchan_id


def test_get_my_shadchan_unregistered_account_is_404(client):
    # authenticated (valid token) but no shadchan row exists for this uid yet
    client.auth_uid["uid"] = "never-registered-uid"

    resp = client.get("/api/v1/shadchanim/me")

    assert resp.status_code == 404


def test_update_shadchan_changes_only_sent_fields(client, shadchan_id):
    resp = client.patch(f"/api/v1/shadchanim/{shadchan_id}", json={"phone": "050-999-0000"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["phone"] == "050-999-0000"
    assert body["name"] == "R. Test"
    assert body["email"] == "test@example.com"


def test_update_shadchan_for_other_shadchan_is_403(client, shadchan_id):
    client.auth_uid["uid"] = "other-firebase-uid"
    client.post(
        "/api/v1/shadchanim",
        json={"name": "R. Other", "phone": "050-222-3333", "email": "other@shadchanim.example"},
    )

    resp = client.patch(f"/api/v1/shadchanim/{shadchan_id}", json={"name": "Hijacked"})

    assert resp.status_code == 403


def test_get_candidates_for_other_shadchan_is_403(client, shadchan_id):
    client.auth_uid["uid"] = "other-firebase-uid"
    other_shadchan_id = client.post(
        "/api/v1/shadchanim",
        json={"name": "R. Other", "phone": "050-222-3333", "email": "other@shadchanim.example"},
    ).json()["id"]

    # still authenticated as "other-firebase-uid" - reaching into the first shadchan's data must 403
    resp = client.get(f"/api/v1/shadchanim/{shadchan_id}/candidates")

    assert resp.status_code == 403
    assert other_shadchan_id != shadchan_id
