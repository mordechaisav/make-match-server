from app.main import app
from app.schemas.pdf_extraction import FemaleCandidateDraft, MaleCandidateDraft, RelativeDraft
from app.services import pdf_extraction_service

RAW_ROWS = {
    "ת. לידה": "24.06.2002",
    "כתובת": "יונתן בני ברק",
    "האב": "יצחק - אברך",
    "אחים": ["דינה, 25, נשואה לנתן רוטשילד"],
}


def _override_male_extractor(draft: MaleCandidateDraft):
    app.dependency_overrides[pdf_extraction_service.get_male_extractor] = lambda: (lambda rows: draft)


def _override_female_extractor(draft: FemaleCandidateDraft):
    app.dependency_overrides[pdf_extraction_service.get_female_extractor] = lambda: (lambda rows: draft)


def test_extract_male_candidate_returns_the_extractor_draft(client, shadchan_id):
    draft = MaleCandidateDraft(
        first_name="Moti",
        last_name=None,
        dob="2002-06-24",
        address="Yonatan, Bnei Brak",
        relatives=[RelativeDraft(relation="father", name="Yitzchak")],
    )
    _override_male_extractor(draft)
    try:
        resp = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates/extract", json={"rows": RAW_ROWS})
    finally:
        app.dependency_overrides.pop(pdf_extraction_service.get_male_extractor, None)

    assert resp.status_code == 200
    body = resp.json()
    assert body["first_name"] == "Moti"
    assert body["last_name"] is None
    assert body["relatives"] == [
        {
            "relation": "father",
            "name": "Yitzchak",
            "maiden_name": None,
            "occupation": None,
            "dob": None,
            "marital_status": None,
            "details": None,
        }
    ]


def test_extract_female_candidate_returns_the_extractor_draft(client, shadchan_id):
    draft = FemaleCandidateDraft(first_name="Miri", last_name="Gold")
    _override_female_extractor(draft)
    try:
        resp = client.post(f"/api/v1/shadchanim/{shadchan_id}/female-candidates/extract", json={"rows": RAW_ROWS})
    finally:
        app.dependency_overrides.pop(pdf_extraction_service.get_female_extractor, None)

    assert resp.status_code == 200
    assert resp.json()["first_name"] == "Miri"


def test_extract_candidate_does_not_persist_anything(client, shadchan_id):
    draft = MaleCandidateDraft(first_name="Moti")
    _override_male_extractor(draft)
    try:
        client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates/extract", json={"rows": RAW_ROWS})
    finally:
        app.dependency_overrides.pop(pdf_extraction_service.get_male_extractor, None)

    listed = client.get(f"/api/v1/shadchanim/{shadchan_id}/candidates").json()
    assert listed["male_candidates"] == []


def test_extract_candidate_for_other_shadchan_is_403(client, shadchan_id):
    client.auth_uid["uid"] = "other-firebase-uid"
    other_shadchan_id = client.post(
        "/api/v1/shadchanim",
        json={"name": "R. Other", "phone": "050-222-3333", "email": "other@shadchanim.example"},
    ).json()["id"]

    resp = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates/extract", json={"rows": RAW_ROWS})

    assert resp.status_code == 403
    assert other_shadchan_id != shadchan_id
