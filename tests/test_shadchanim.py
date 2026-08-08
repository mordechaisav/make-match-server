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


def test_register_shadchan_without_token_is_401(client_no_auth_override):
    resp = client_no_auth_override.post(
        "/api/v1/shadchanim",
        json={"name": "R. Cohen", "phone": "050-111-2222", "email": "cohen@shadchanim.example"},
    )

    assert resp.status_code == 401


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
