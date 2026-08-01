MALE_BODY = {
    "first_name": "Aryeh",
    "last_name": "Stein",
    "dob": "1996-02-14",
    "height": 178,
    "address": "Lakewood",
    "talmud_torah": "TT Lakewood",
    "yeshiva_ketana": "Yeshiva Ketana X",
}

FEMALE_BODY = {
    "first_name": "Miri",
    "last_name": "Gold",
    "dob": "2001-07-09",
    "height": 158,
}


# ---- create ----


def test_create_male_candidate_returns_full_shape(client, shadchan_id):
    resp = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=MALE_BODY)

    assert resp.status_code == 201
    body = resp.json()
    assert body["shadchan_id"] == shadchan_id
    assert body["first_name"] == "Aryeh"
    assert body["talmud_torah"] == "TT Lakewood"
    assert body["yeshiva_ketana"] == "Yeshiva Ketana X"
    assert body["yeshiva_gedola"] is None
    assert body["relatives"] == []
    assert body["references"] == []


def test_create_female_candidate_returns_full_shape(client, shadchan_id):
    resp = client.post(f"/api/v1/shadchanim/{shadchan_id}/female-candidates", json=FEMALE_BODY)

    assert resp.status_code == 201
    body = resp.json()
    assert body["shadchan_id"] == shadchan_id
    assert body["first_name"] == "Miri"
    assert body["beit_yaakov"] is None
    assert body["seminar"] is None
    assert body["maslul"] is None
    assert body["address"] is None


def test_create_male_candidate_minimal_body_leaves_optionals_null(client, shadchan_id):
    resp = client.post(
        f"/api/v1/shadchanim/{shadchan_id}/male-candidates",
        json={"first_name": "X", "last_name": "Y", "dob": "2000-01-01"},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["height"] is None
    assert body["address"] is None
    assert body["talmud_torah"] is None
    assert body["yeshiva_ketana"] is None
    assert body["yeshiva_gedola"] is None


def test_create_candidate_missing_required_field_is_422(client, shadchan_id):
    resp = client.post(
        f"/api/v1/shadchanim/{shadchan_id}/male-candidates",
        json={"first_name": "Aryeh", "dob": "1996-02-14"},
    )

    assert resp.status_code == 422


def test_create_male_candidate_unknown_shadchan_is_404(client):
    resp = client.post("/api/v1/shadchanim/999999/male-candidates", json=MALE_BODY)

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Shadchan not found"


def test_create_female_candidate_unknown_shadchan_is_404(client):
    resp = client.post("/api/v1/shadchanim/999999/female-candidates", json=FEMALE_BODY)

    assert resp.status_code == 404


# ---- update ----


def test_update_male_candidate_changes_only_sent_fields(client, shadchan_id):
    created = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=MALE_BODY).json()

    resp = client.patch(
        f"/api/v1/shadchanim/{shadchan_id}/male-candidates/{created['id']}",
        json={"yeshiva_gedola": "Mir Yerushalayim"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["yeshiva_gedola"] == "Mir Yerushalayim"
    # untouched fields survive the partial update
    assert body["first_name"] == "Aryeh"
    assert body["talmud_torah"] == "TT Lakewood"
    assert body["yeshiva_ketana"] == "Yeshiva Ketana X"
    assert body["address"] == "Lakewood"


def test_update_female_candidate_changes_only_sent_fields(client, shadchan_id):
    created = client.post(f"/api/v1/shadchanim/{shadchan_id}/female-candidates", json=FEMALE_BODY).json()

    resp = client.patch(
        f"/api/v1/shadchanim/{shadchan_id}/female-candidates/{created['id']}",
        json={"address": "Monsey", "seminar": "Seminar Bnos Yerushalayim"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["address"] == "Monsey"
    assert body["seminar"] == "Seminar Bnos Yerushalayim"
    assert body["first_name"] == "Miri"
    assert body["beit_yaakov"] is None


def test_update_candidate_unknown_shadchan_is_404(client, shadchan_id):
    created = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=MALE_BODY).json()

    resp = client.patch(
        f"/api/v1/shadchanim/999999/male-candidates/{created['id']}", json={"height": 190}
    )

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Shadchan not found"


def test_update_candidate_nonexistent_candidate_is_404(client, shadchan_id):
    resp = client.patch(
        f"/api/v1/shadchanim/{shadchan_id}/male-candidates/999999", json={"height": 190}
    )

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Male candidate not found"


def test_update_candidate_wrong_shadchan_scope_is_404(client, shadchan_id):
    other_shadchan_id = client.post(
        "/api/v1/shadchanim",
        json={"name": "R. Other", "phone": "050-222-3333", "email": "other@shadchanim.example"},
    ).json()["id"]
    created = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=MALE_BODY).json()

    # candidate exists, but not under other_shadchan_id -> must 404, not leak across shadchanim
    resp = client.patch(
        f"/api/v1/shadchanim/{other_shadchan_id}/male-candidates/{created['id']}",
        json={"height": 190},
    )

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Male candidate not found"


# ---- list ----


def test_get_candidates_lists_created_candidates(client, shadchan_id):
    client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=MALE_BODY)
    client.post(f"/api/v1/shadchanim/{shadchan_id}/female-candidates", json=FEMALE_BODY)

    resp = client.get(f"/api/v1/shadchanim/{shadchan_id}/candidates")

    assert resp.status_code == 200
    body = resp.json()
    assert len(body["male_candidates"]) == 1
    assert len(body["female_candidates"]) == 1
    assert body["pagination"] == {"limit": 50, "offset": 0, "male_total": 1, "female_total": 1}


def test_get_candidates_unknown_shadchan_is_404(client):
    resp = client.get("/api/v1/shadchanim/999999/candidates")

    assert resp.status_code == 404


def test_get_candidates_pagination_applies_per_gender_list(client, shadchan_id):
    for i in range(3):
        client.post(
            f"/api/v1/shadchanim/{shadchan_id}/male-candidates",
            json={"first_name": f"M{i}", "last_name": "Test", "dob": "2000-01-01"},
        )

    resp = client.get(f"/api/v1/shadchanim/{shadchan_id}/candidates?limit=1&offset=0")

    assert resp.status_code == 200
    body = resp.json()
    assert len(body["male_candidates"]) == 1
    assert body["pagination"]["male_total"] == 3
