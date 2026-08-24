from datetime import date


def _dob_for_age(age: int) -> str:
    today = date.today()
    try:
        return today.replace(year=today.year - age).isoformat()
    except ValueError:
        return today.replace(month=2, day=28, year=today.year - age).isoformat()


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


def test_create_male_candidate_unknown_shadchan_is_403(client, shadchan_id):
    # authenticated shadchan (shadchan_id) has no claim over this unrelated id
    resp = client.post("/api/v1/shadchanim/999999/male-candidates", json=MALE_BODY)

    assert resp.status_code == 403


def test_create_female_candidate_unknown_shadchan_is_403(client, shadchan_id):
    resp = client.post("/api/v1/shadchanim/999999/female-candidates", json=FEMALE_BODY)

    assert resp.status_code == 403


# ---- relatives & references ----


def test_create_male_candidate_with_relatives_and_references(client, shadchan_id):
    body = {
        **MALE_BODY,
        "relatives": [
            {"relation": "father", "name": "Yitzchak", "occupation": "Avreich"},
            {"relation": "mother", "name": "Rivka", "maiden_name": "Mandinger", "occupation": "Teacher"},
            {"relation": "sibling", "name": "Dina", "dob": "2001-01-01", "marital_status": "married"},
        ],
        "references": [
            {"ref_type": "rabbi_teacher", "name": "R. Halman", "role_connection": "Rav biyeshiva", "phone": "0555555555"},
            {"ref_type": "friend", "name": "Moshe Cohen", "phone": "0555552555"},
        ],
    }

    resp = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=body)

    assert resp.status_code == 201
    created = resp.json()
    assert len(created["relatives"]) == 3
    assert {r["relation"] for r in created["relatives"]} == {"father", "mother", "sibling"}
    mother = next(r for r in created["relatives"] if r["relation"] == "mother")
    assert mother["maiden_name"] == "Mandinger"
    assert len(created["references"]) == 2
    assert {r["ref_type"] for r in created["references"]} == {"rabbi_teacher", "friend"}

    # persisted, not just echoed back - refetch via the list endpoint
    listed = client.get(f"/api/v1/shadchanim/{shadchan_id}/candidates").json()
    assert len(listed["male_candidates"][0]["relatives"]) == 3


def test_create_female_candidate_omitting_relatives_and_references_defaults_to_empty(client, shadchan_id):
    resp = client.post(f"/api/v1/shadchanim/{shadchan_id}/female-candidates", json=FEMALE_BODY)

    assert resp.status_code == 201
    body = resp.json()
    assert body["relatives"] == []
    assert body["references"] == []


# ---- get single ----


def test_get_male_candidate_returns_full_shape(client, shadchan_id):
    created = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=MALE_BODY).json()

    resp = client.get(f"/api/v1/shadchanim/{shadchan_id}/male-candidates/{created['id']}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == created["id"]
    assert body["first_name"] == "Aryeh"


def test_get_female_candidate_returns_full_shape(client, shadchan_id):
    created = client.post(f"/api/v1/shadchanim/{shadchan_id}/female-candidates", json=FEMALE_BODY).json()

    resp = client.get(f"/api/v1/shadchanim/{shadchan_id}/female-candidates/{created['id']}")

    assert resp.status_code == 200
    assert resp.json()["first_name"] == "Miri"


def test_get_male_candidate_nonexistent_is_404(client, shadchan_id):
    resp = client.get(f"/api/v1/shadchanim/{shadchan_id}/male-candidates/999999")

    assert resp.status_code == 404


def test_get_male_candidate_unknown_shadchan_is_403(client, shadchan_id):
    created = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=MALE_BODY).json()

    resp = client.get(f"/api/v1/shadchanim/999999/male-candidates/{created['id']}")

    assert resp.status_code == 403


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


def test_update_male_candidate_clears_field_with_explicit_null(client, shadchan_id):
    created = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=MALE_BODY).json()

    resp = client.patch(
        f"/api/v1/shadchanim/{shadchan_id}/male-candidates/{created['id']}",
        json={"height": None, "picture_url": None},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["height"] is None
    assert body["picture_url"] is None
    # untouched
    assert body["address"] == "Lakewood"


def test_update_male_candidate_omitting_relatives_leaves_them_untouched(client, shadchan_id):
    body = {**MALE_BODY, "relatives": [{"relation": "father", "name": "Yitzchak"}]}
    created = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=body).json()

    resp = client.patch(
        f"/api/v1/shadchanim/{shadchan_id}/male-candidates/{created['id']}",
        json={"height": 180},
    )

    assert resp.status_code == 200
    assert len(resp.json()["relatives"]) == 1
    assert resp.json()["relatives"][0]["name"] == "Yitzchak"


def test_update_male_candidate_empty_relatives_list_clears_them(client, shadchan_id):
    body = {**MALE_BODY, "relatives": [{"relation": "father", "name": "Yitzchak"}]}
    created = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=body).json()

    resp = client.patch(
        f"/api/v1/shadchanim/{shadchan_id}/male-candidates/{created['id']}",
        json={"relatives": []},
    )

    assert resp.status_code == 200
    assert resp.json()["relatives"] == []


def test_update_male_candidate_replaces_relatives_and_references(client, shadchan_id):
    body = {
        **MALE_BODY,
        "relatives": [{"relation": "father", "name": "Yitzchak"}],
        "references": [{"ref_type": "friend", "name": "Moshe Cohen"}],
    }
    created = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=body).json()

    resp = client.patch(
        f"/api/v1/shadchanim/{shadchan_id}/male-candidates/{created['id']}",
        json={
            "relatives": [{"relation": "mother", "name": "Rivka", "maiden_name": "Mandinger"}],
            "references": [{"ref_type": "rabbi_teacher", "name": "R. Halman"}],
        },
    )

    assert resp.status_code == 200
    updated = resp.json()
    assert len(updated["relatives"]) == 1
    assert updated["relatives"][0]["relation"] == "mother"
    assert updated["relatives"][0]["maiden_name"] == "Mandinger"
    assert len(updated["references"]) == 1
    assert updated["references"][0]["name"] == "R. Halman"

    # replacement persisted, not just echoed back
    refetched = client.get(f"/api/v1/shadchanim/{shadchan_id}/male-candidates/{created['id']}").json()
    assert len(refetched["relatives"]) == 1
    assert refetched["relatives"][0]["name"] == "Rivka"


def test_update_female_candidate_replaces_relatives(client, shadchan_id):
    body = {**FEMALE_BODY, "relatives": [{"relation": "sibling", "name": "Dina"}]}
    created = client.post(f"/api/v1/shadchanim/{shadchan_id}/female-candidates", json=body).json()

    resp = client.patch(
        f"/api/v1/shadchanim/{shadchan_id}/female-candidates/{created['id']}",
        json={"relatives": [{"relation": "mother", "name": "Sarah"}]},
    )

    assert resp.status_code == 200
    assert [r["name"] for r in resp.json()["relatives"]] == ["Sarah"]


# ---- favourites & notes ----


def test_create_male_candidate_favourite_and_notes_round_trip(client, shadchan_id):
    resp = client.post(
        f"/api/v1/shadchanim/{shadchan_id}/male-candidates",
        json={**MALE_BODY, "is_favourite": True, "notes": "met at a vort"},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["is_favourite"] is True
    assert body["notes"] == "met at a vort"


def test_create_male_candidate_defaults_is_favourite_false(client, shadchan_id):
    resp = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=MALE_BODY)

    assert resp.status_code == 201
    body = resp.json()
    assert body["is_favourite"] is False
    assert body["notes"] is None


def test_update_male_candidate_sets_favourite_and_notes(client, shadchan_id):
    created = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=MALE_BODY).json()

    resp = client.patch(
        f"/api/v1/shadchanim/{shadchan_id}/male-candidates/{created['id']}",
        json={"is_favourite": True, "notes": "follow up next week"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["is_favourite"] is True
    assert body["notes"] == "follow up next week"


def test_get_candidates_favourites_only_filters(client, shadchan_id):
    _create_male(client, shadchan_id, first_name="Fav", is_favourite=True)
    _create_male(client, shadchan_id, first_name="NotFav", is_favourite=False)

    resp = client.get(f"/api/v1/shadchanim/{shadchan_id}/candidates?favourites_only=true")

    assert resp.status_code == 200
    names = [c["first_name"] for c in resp.json()["male_candidates"]]
    assert names == ["Fav"]


def test_update_candidate_unknown_shadchan_is_403(client, shadchan_id):
    created = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=MALE_BODY).json()

    resp = client.patch(
        f"/api/v1/shadchanim/999999/male-candidates/{created['id']}", json={"height": 190}
    )

    assert resp.status_code == 403


def test_update_candidate_nonexistent_candidate_is_404(client, shadchan_id):
    resp = client.patch(
        f"/api/v1/shadchanim/{shadchan_id}/male-candidates/999999", json={"height": 190}
    )

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Male candidate not found"


def test_update_candidate_wrong_shadchan_scope_is_404(client, shadchan_id):
    created = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=MALE_BODY).json()

    # a second, distinct authenticated shadchan - legitimately allowed to hit ITS OWN
    # shadchan_id (passes the ownership check), but the candidate belongs to shadchan_id, not this one
    client.auth_uid["uid"] = "other-firebase-uid"
    other_shadchan_id = client.post(
        "/api/v1/shadchanim",
        json={"name": "R. Other", "phone": "050-222-3333", "email": "other@shadchanim.example"},
    ).json()["id"]

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


def test_get_candidates_unknown_shadchan_is_403(client):
    resp = client.get("/api/v1/shadchanim/999999/candidates")

    assert resp.status_code == 403


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


# ---- filters ----


def _create_male(client, shadchan_id, **overrides):
    body = {"first_name": "M", "last_name": "Test", "dob": "2000-01-01", **overrides}
    resp = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=body)
    assert resp.status_code == 201
    return resp.json()


def test_get_candidates_filters_by_age_range(client, shadchan_id):
    _create_male(client, shadchan_id, first_name="Young", dob=_dob_for_age(20))
    _create_male(client, shadchan_id, first_name="Mid", dob=_dob_for_age(28))
    _create_male(client, shadchan_id, first_name="Old", dob=_dob_for_age(40))

    resp = client.get(f"/api/v1/shadchanim/{shadchan_id}/candidates?age_min=25&age_max=35")

    assert resp.status_code == 200
    names = {c["first_name"] for c in resp.json()["male_candidates"]}
    assert names == {"Mid"}
    assert resp.json()["pagination"]["male_total"] == 1


def test_get_candidates_filters_by_height_range(client, shadchan_id):
    _create_male(client, shadchan_id, first_name="Short", height=160)
    _create_male(client, shadchan_id, first_name="Tall", height=190)

    resp = client.get(f"/api/v1/shadchanim/{shadchan_id}/candidates?height_min=180")

    body = resp.json()
    assert resp.status_code == 200
    assert [c["first_name"] for c in body["male_candidates"]] == ["Tall"]
    assert body["pagination"]["male_total"] == 1


def test_get_candidates_filters_by_address_substring_case_insensitive(client, shadchan_id):
    _create_male(client, shadchan_id, first_name="Local", address="Lakewood, NJ")
    _create_male(client, shadchan_id, first_name="Away", address="Monsey, NY")

    resp = client.get(f"/api/v1/shadchanim/{shadchan_id}/candidates?address=lakewood")

    body = resp.json()
    assert resp.status_code == 200
    assert [c["first_name"] for c in body["male_candidates"]] == ["Local"]
    assert body["pagination"]["male_total"] == 1


def test_get_candidates_combined_filters_apply_together(client, shadchan_id):
    _create_male(client, shadchan_id, first_name="Match", dob=_dob_for_age(28), height=185, address="Lakewood")
    _create_male(client, shadchan_id, first_name="WrongHeight", dob=_dob_for_age(28), height=160, address="Lakewood")
    _create_male(client, shadchan_id, first_name="WrongAddress", dob=_dob_for_age(28), height=185, address="Monsey")

    resp = client.get(
        f"/api/v1/shadchanim/{shadchan_id}/candidates?age_min=25&age_max=35&height_min=180&address=lakewood"
    )

    body = resp.json()
    assert resp.status_code == 200
    assert [c["first_name"] for c in body["male_candidates"]] == ["Match"]


def test_get_candidates_filters_by_name_substring_matches_first_or_last(client, shadchan_id):
    _create_male(client, shadchan_id, first_name="Aryeh", last_name="Stein")
    _create_male(client, shadchan_id, first_name="Moshe", last_name="Steinberg")
    _create_male(client, shadchan_id, first_name="Yankel", last_name="Cohen")

    resp = client.get(f"/api/v1/shadchanim/{shadchan_id}/candidates?name=stein")

    body = resp.json()
    assert resp.status_code == 200
    assert {c["first_name"] for c in body["male_candidates"]} == {"Aryeh", "Moshe"}
    assert body["pagination"]["male_total"] == 2


def test_get_candidates_no_filters_returns_everyone(client, shadchan_id):
    _create_male(client, shadchan_id, first_name="A")
    _create_male(client, shadchan_id, first_name="B")

    resp = client.get(f"/api/v1/shadchanim/{shadchan_id}/candidates")

    assert resp.status_code == 200
    assert len(resp.json()["male_candidates"]) == 2
