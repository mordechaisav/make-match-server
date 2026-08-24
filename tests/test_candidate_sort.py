def _create_male(client, shadchan_id, **overrides):
    body = {"first_name": "M", "last_name": "Test", "dob": "2000-01-01", **overrides}
    resp = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=body)
    assert resp.status_code == 201
    return resp.json()


def test_sort_created_desc_is_default(client, shadchan_id):
    first = _create_male(client, shadchan_id, first_name="First")
    second = _create_male(client, shadchan_id, first_name="Second")

    resp = client.get(f"/api/v1/shadchanim/{shadchan_id}/candidates")

    ids = [c["id"] for c in resp.json()["male_candidates"]]
    assert ids == [second["id"], first["id"]]


def test_sort_created_asc(client, shadchan_id):
    first = _create_male(client, shadchan_id, first_name="First")
    second = _create_male(client, shadchan_id, first_name="Second")

    resp = client.get(f"/api/v1/shadchanim/{shadchan_id}/candidates?sort=created_asc")

    ids = [c["id"] for c in resp.json()["male_candidates"]]
    assert ids == [first["id"], second["id"]]


def test_sort_age_asc_youngest_first(client, shadchan_id):
    _create_male(client, shadchan_id, first_name="Older", dob="1990-01-01")
    _create_male(client, shadchan_id, first_name="Younger", dob="2005-01-01")

    resp = client.get(f"/api/v1/shadchanim/{shadchan_id}/candidates?sort=age_asc")

    names = [c["first_name"] for c in resp.json()["male_candidates"]]
    assert names == ["Younger", "Older"]


def test_sort_age_desc_oldest_first(client, shadchan_id):
    _create_male(client, shadchan_id, first_name="Older", dob="1990-01-01")
    _create_male(client, shadchan_id, first_name="Younger", dob="2005-01-01")

    resp = client.get(f"/api/v1/shadchanim/{shadchan_id}/candidates?sort=age_desc")

    names = [c["first_name"] for c in resp.json()["male_candidates"]]
    assert names == ["Older", "Younger"]


def test_sort_name_asc(client, shadchan_id):
    _create_male(client, shadchan_id, first_name="Zev", last_name="Aaronson")
    _create_male(client, shadchan_id, first_name="Aryeh", last_name="Zimmerman")

    resp = client.get(f"/api/v1/shadchanim/{shadchan_id}/candidates?sort=name_asc")

    last_names = [c["last_name"] for c in resp.json()["male_candidates"]]
    assert last_names == ["Aaronson", "Zimmerman"]


def test_sort_name_desc(client, shadchan_id):
    _create_male(client, shadchan_id, first_name="Zev", last_name="Aaronson")
    _create_male(client, shadchan_id, first_name="Aryeh", last_name="Zimmerman")

    resp = client.get(f"/api/v1/shadchanim/{shadchan_id}/candidates?sort=name_desc")

    last_names = [c["last_name"] for c in resp.json()["male_candidates"]]
    assert last_names == ["Zimmerman", "Aaronson"]


def test_sort_applies_to_female_list_too(client, shadchan_id):
    first = client.post(
        f"/api/v1/shadchanim/{shadchan_id}/female-candidates",
        json={"first_name": "First", "last_name": "F", "dob": "2000-01-01"},
    ).json()
    second = client.post(
        f"/api/v1/shadchanim/{shadchan_id}/female-candidates",
        json={"first_name": "Second", "last_name": "S", "dob": "2000-01-01"},
    ).json()

    resp = client.get(f"/api/v1/shadchanim/{shadchan_id}/candidates?sort=created_asc")

    ids = [c["id"] for c in resp.json()["female_candidates"]]
    assert ids == [first["id"], second["id"]]


def test_sort_invalid_value_is_422(client, shadchan_id):
    resp = client.get(f"/api/v1/shadchanim/{shadchan_id}/candidates?sort=not_a_real_sort")

    assert resp.status_code == 422
