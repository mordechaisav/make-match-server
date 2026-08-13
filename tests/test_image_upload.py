from app.main import app
from app.schemas.image import UploadUrlOut
from app.services import image_service

MALE_BODY = {
    "first_name": "Moti",
    "last_name": "Cohen",
    "dob": "2000-01-01",
}


def _override_upload_url_generator(fake):
    app.dependency_overrides[image_service.get_upload_url_generator] = lambda: fake


def _override_object_checker(exists: bool):
    app.dependency_overrides[image_service.get_object_checker] = lambda: (lambda key: exists)


def _override_read_url_generator(signed_url: str):
    app.dependency_overrides[image_service.get_read_url_generator] = lambda: (lambda key: signed_url)


def test_create_upload_url_returns_generator_output(client, shadchan_id):
    calls = []

    def fake_generate(shadchan_id_arg, content_type):
        calls.append((shadchan_id_arg, content_type))
        return UploadUrlOut(upload_url="https://b2.example/put?sig=abc", path="candidates/1/x.jpg", expires_in=300)

    _override_upload_url_generator(fake_generate)
    try:
        resp = client.post(f"/api/v1/shadchanim/{shadchan_id}/upload-url", json={"content_type": "image/jpeg"})
    finally:
        app.dependency_overrides.pop(image_service.get_upload_url_generator, None)

    assert resp.status_code == 200
    body = resp.json()
    assert body["upload_url"] == "https://b2.example/put?sig=abc"
    assert body["path"] == "candidates/1/x.jpg"
    assert body["expires_in"] == 300
    assert calls == [(shadchan_id, "image/jpeg")]


def test_create_upload_url_for_other_shadchan_is_403(client, shadchan_id):
    client.auth_uid["uid"] = "other-firebase-uid"
    other_shadchan_id = client.post(
        "/api/v1/shadchanim",
        json={"name": "R. Other", "phone": "050-222-3333", "email": "other@shadchanim.example"},
    ).json()["id"]

    resp = client.post(f"/api/v1/shadchanim/{shadchan_id}/upload-url", json={"content_type": "image/jpeg"})

    assert resp.status_code == 403
    assert other_shadchan_id != shadchan_id


def test_create_candidate_with_existing_picture_resolves_to_signed_url(client, shadchan_id):
    _override_object_checker(True)
    _override_read_url_generator("https://b2.example/get?sig=xyz")
    try:
        resp = client.post(
            f"/api/v1/shadchanim/{shadchan_id}/male-candidates",
            json={**MALE_BODY, "picture_url": "candidates/1/x.jpg"},
        )
    finally:
        app.dependency_overrides.pop(image_service.get_object_checker, None)
        app.dependency_overrides.pop(image_service.get_read_url_generator, None)

    assert resp.status_code == 201
    assert resp.json()["picture_url"] == "https://b2.example/get?sig=xyz"


def test_create_candidate_with_missing_picture_is_400(client, shadchan_id):
    _override_object_checker(False)
    try:
        resp = client.post(
            f"/api/v1/shadchanim/{shadchan_id}/male-candidates",
            json={**MALE_BODY, "picture_url": "candidates/1/does-not-exist.jpg"},
        )
    finally:
        app.dependency_overrides.pop(image_service.get_object_checker, None)

    assert resp.status_code == 400

    listed = client.get(f"/api/v1/shadchanim/{shadchan_id}/candidates").json()
    assert listed["male_candidates"] == []


def test_create_candidate_without_picture_never_calls_b2(client, shadchan_id):
    resp = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates", json=MALE_BODY)

    assert resp.status_code == 201
    assert resp.json()["picture_url"] is None
