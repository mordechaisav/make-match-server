from app.main import app
from app.services import image_service

MALE_BODY = {"first_name": "Aryeh", "last_name": "Stein", "dob": "1996-02-14"}
FEMALE_BODY = {"first_name": "Miri", "last_name": "Gold", "dob": "2001-07-09"}


def _override_object_deleter():
    calls = []
    app.dependency_overrides[image_service.get_object_deleter] = lambda: (lambda key: calls.append(key))
    return calls


def test_delete_male_candidate_returns_204_and_removes_it(client, shadchan_id):
    _override_object_deleter()
    try:
        created = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=MALE_BODY).json()

        resp = client.delete(f"/api/v1/shadchanim/{shadchan_id}/male-candidates/{created['id']}")

        assert resp.status_code == 204
        assert resp.content == b""
        assert client.get(f"/api/v1/shadchanim/{shadchan_id}/male-candidates/{created['id']}").status_code == 404
    finally:
        app.dependency_overrides.pop(image_service.get_object_deleter, None)


def test_delete_female_candidate_returns_204_and_removes_it(client, shadchan_id):
    _override_object_deleter()
    try:
        created = client.post(f"/api/v1/shadchanim/{shadchan_id}/female-candidates", json=FEMALE_BODY).json()

        resp = client.delete(f"/api/v1/shadchanim/{shadchan_id}/female-candidates/{created['id']}")

        assert resp.status_code == 204
        assert client.get(f"/api/v1/shadchanim/{shadchan_id}/female-candidates/{created['id']}").status_code == 404
    finally:
        app.dependency_overrides.pop(image_service.get_object_deleter, None)


def test_delete_male_candidate_cascades_relatives_and_references(client, shadchan_id):
    _override_object_deleter()
    try:
        body = {
            **MALE_BODY,
            "relatives": [{"relation": "father", "name": "Yitzchak"}],
            "references": [{"ref_type": "friend", "name": "Moshe Cohen"}],
        }
        created = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=body).json()

        resp = client.delete(f"/api/v1/shadchanim/{shadchan_id}/male-candidates/{created['id']}")

        assert resp.status_code == 204
        listed = client.get(f"/api/v1/shadchanim/{shadchan_id}/candidates").json()
        assert listed["male_candidates"] == []
    finally:
        app.dependency_overrides.pop(image_service.get_object_deleter, None)


def test_delete_male_candidate_best_effort_deletes_b2_object(client, shadchan_id):
    calls = _override_object_deleter()
    from app.services import image_service as image_service_module

    app.dependency_overrides[image_service_module.get_object_checker] = lambda: (lambda key: True)
    try:
        created = client.post(
            f"/api/v1/shadchanim/{shadchan_id}/male-candidates",
            json={**MALE_BODY, "picture_url": "candidates/1/x.jpg"},
        ).json()

        resp = client.delete(f"/api/v1/shadchanim/{shadchan_id}/male-candidates/{created['id']}")

        assert resp.status_code == 204
        assert calls == ["candidates/1/x.jpg"]
    finally:
        app.dependency_overrides.pop(image_service.get_object_deleter, None)
        app.dependency_overrides.pop(image_service_module.get_object_checker, None)


def test_delete_male_candidate_without_picture_never_calls_b2(client, shadchan_id):
    calls = _override_object_deleter()
    try:
        created = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=MALE_BODY).json()

        resp = client.delete(f"/api/v1/shadchanim/{shadchan_id}/male-candidates/{created['id']}")

        assert resp.status_code == 204
        assert calls == []
    finally:
        app.dependency_overrides.pop(image_service.get_object_deleter, None)


def test_delete_male_candidate_unknown_shadchan_is_403(client, shadchan_id):
    _override_object_deleter()
    try:
        created = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=MALE_BODY).json()

        resp = client.delete(f"/api/v1/shadchanim/999999/male-candidates/{created['id']}")

        assert resp.status_code == 403
    finally:
        app.dependency_overrides.pop(image_service.get_object_deleter, None)


def test_delete_male_candidate_nonexistent_is_404(client, shadchan_id):
    _override_object_deleter()
    try:
        resp = client.delete(f"/api/v1/shadchanim/{shadchan_id}/male-candidates/999999")

        assert resp.status_code == 404
    finally:
        app.dependency_overrides.pop(image_service.get_object_deleter, None)


def test_delete_male_candidate_wrong_shadchan_scope_is_404(client, shadchan_id):
    _override_object_deleter()
    try:
        created = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=MALE_BODY).json()

        client.auth_uid["uid"] = "other-firebase-uid"
        other_shadchan_id = client.post(
            "/api/v1/shadchanim",
            json={"name": "R. Other", "phone": "050-222-3333", "email": "other@shadchanim.example"},
        ).json()["id"]

        resp = client.delete(f"/api/v1/shadchanim/{other_shadchan_id}/male-candidates/{created['id']}")

        assert resp.status_code == 404
    finally:
        app.dependency_overrides.pop(image_service.get_object_deleter, None)
