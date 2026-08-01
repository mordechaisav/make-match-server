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
