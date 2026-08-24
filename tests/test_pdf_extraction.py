import io

import docx
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from app.main import app
from app.schemas.pdf_extraction import FemaleCandidateDraft, MaleCandidateDraft, RelativeDraft
from app.services import document_text_service, pdf_extraction_service


def _build_pdf_bytes(text: str) -> bytes:
    """A minimal real PDF containing `text`, built entirely through pypdf's
    writer API (no hand-rolled byte offsets) so tests exercise real parsing.
    """
    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=200)

    stream_obj = DecodedStreamObject()
    stream_obj.set_data(f"BT /F1 24 Tf 10 100 Td ({text}) Tj ET".encode("latin-1"))
    content_ref = writer._add_object(stream_obj)

    font_dict = DictionaryObject()
    font_dict[NameObject("/Type")] = NameObject("/Font")
    font_dict[NameObject("/Subtype")] = NameObject("/Type1")
    font_dict[NameObject("/BaseFont")] = NameObject("/Helvetica")
    font_ref = writer._add_object(font_dict)

    resources = DictionaryObject()
    font_res = DictionaryObject()
    font_res[NameObject("/F1")] = font_ref
    resources[NameObject("/Font")] = font_res

    page[NameObject("/Contents")] = content_ref
    page[NameObject("/Resources")] = resources

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _build_docx_bytes(paragraphs: list[str]) -> bytes:
    document = docx.Document()
    for text in paragraphs:
        document.add_paragraph(text)
    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()


RAW_TEXT = """\
ת. לידה: 24.06.2002
כתובת: יונתן בני ברק
האב: יצחק - אברך
אחים: דינה, 25, נשואה לנתן רוטשילד
"""


def _override_text_extractor(text: str):
    app.dependency_overrides[document_text_service.get_text_extractor] = lambda: (lambda file: text)


def _override_male_extractor(draft: MaleCandidateDraft):
    app.dependency_overrides[pdf_extraction_service.get_male_extractor] = lambda: (lambda text: draft)


def _override_female_extractor(draft: FemaleCandidateDraft):
    app.dependency_overrides[pdf_extraction_service.get_female_extractor] = lambda: (lambda text: draft)


def _post_file(client, shadchan_id, gender, filename, content, content_type):
    return client.post(
        f"/api/v1/shadchanim/{shadchan_id}/{gender}-candidates/extract",
        files={"file": (filename, content, content_type)},
    )


# ---- routing / end-to-end (extractors mocked) ----


def test_extract_male_candidate_returns_the_extractor_draft(client, shadchan_id):
    draft = MaleCandidateDraft(
        first_name="Moti",
        last_name=None,
        dob="2002-06-24",
        address="Yonatan, Bnei Brak",
        relatives=[RelativeDraft(relation="father", name="Yitzchak")],
    )
    _override_text_extractor(RAW_TEXT)
    _override_male_extractor(draft)
    try:
        resp = _post_file(client, shadchan_id, "male", "resume.pdf", b"whatever", "application/pdf")
    finally:
        app.dependency_overrides.pop(document_text_service.get_text_extractor, None)
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


def test_extract_male_candidate_includes_notes_for_unmapped_text(client, shadchan_id):
    draft = MaleCandidateDraft(first_name="Moti", notes="תחביבים: כדורגל\nמידות: רגוע")
    _override_text_extractor(RAW_TEXT)
    _override_male_extractor(draft)
    try:
        resp = _post_file(client, shadchan_id, "male", "resume.pdf", b"whatever", "application/pdf")
    finally:
        app.dependency_overrides.pop(document_text_service.get_text_extractor, None)
        app.dependency_overrides.pop(pdf_extraction_service.get_male_extractor, None)

    assert resp.status_code == 200
    assert resp.json()["notes"] == "תחביבים: כדורגל\nמידות: רגוע"


def test_extract_female_candidate_returns_the_extractor_draft(client, shadchan_id):
    draft = FemaleCandidateDraft(first_name="Miri", last_name="Gold")
    _override_text_extractor(RAW_TEXT)
    _override_female_extractor(draft)
    try:
        resp = _post_file(client, shadchan_id, "female", "resume.docx", b"whatever", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    finally:
        app.dependency_overrides.pop(document_text_service.get_text_extractor, None)
        app.dependency_overrides.pop(pdf_extraction_service.get_female_extractor, None)

    assert resp.status_code == 200
    assert resp.json()["first_name"] == "Miri"


def test_extract_candidate_does_not_persist_anything(client, shadchan_id):
    draft = MaleCandidateDraft(first_name="Moti")
    _override_text_extractor(RAW_TEXT)
    _override_male_extractor(draft)
    try:
        _post_file(client, shadchan_id, "male", "resume.pdf", b"whatever", "application/pdf")
    finally:
        app.dependency_overrides.pop(document_text_service.get_text_extractor, None)
        app.dependency_overrides.pop(pdf_extraction_service.get_male_extractor, None)

    listed = client.get(f"/api/v1/shadchanim/{shadchan_id}/candidates").json()
    assert listed["male_candidates"] == []


def test_extract_candidate_for_other_shadchan_is_403(client, shadchan_id):
    client.auth_uid["uid"] = "other-firebase-uid"
    other_shadchan_id = client.post(
        "/api/v1/shadchanim",
        json={"name": "R. Other", "phone": "050-222-3333", "email": "other@shadchanim.example"},
    ).json()["id"]

    resp = _post_file(client, shadchan_id, "male", "resume.pdf", b"whatever", "application/pdf")

    assert resp.status_code == 403
    assert other_shadchan_id != shadchan_id


def test_extract_candidate_missing_file_is_422(client, shadchan_id):
    resp = client.post(f"/api/v1/shadchanim/{shadchan_id}/male-candidates/extract")

    assert resp.status_code == 422


# ---- real file parsing (document_text_service, no mocking) ----


def test_extract_pdf_parses_real_pdf_text(client, shadchan_id):
    pdf_bytes = _build_pdf_bytes("Hello World")
    _override_male_extractor(MaleCandidateDraft(first_name="Moti"))
    captured = {}
    original = document_text_service.extract_text_from_upload

    def spy(file):
        captured["text"] = original(file)
        return captured["text"]

    app.dependency_overrides[document_text_service.get_text_extractor] = lambda: spy
    try:
        resp = _post_file(client, shadchan_id, "male", "resume.pdf", pdf_bytes, "application/pdf")
    finally:
        app.dependency_overrides.pop(document_text_service.get_text_extractor, None)
        app.dependency_overrides.pop(pdf_extraction_service.get_male_extractor, None)

    assert resp.status_code == 200
    assert "Hello World" in captured["text"]


def test_extract_docx_parses_real_docx_text(client, shadchan_id):
    docx_bytes = _build_docx_bytes(["ת. לידה: 24.06.2002", "כתובת: בני ברק"])
    _override_male_extractor(MaleCandidateDraft(first_name="Moti"))
    captured = {}
    original = document_text_service.extract_text_from_upload

    def spy(file):
        captured["text"] = original(file)
        return captured["text"]

    app.dependency_overrides[document_text_service.get_text_extractor] = lambda: spy
    try:
        resp = _post_file(
            client,
            shadchan_id,
            "male",
            "resume.docx",
            docx_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    finally:
        app.dependency_overrides.pop(document_text_service.get_text_extractor, None)
        app.dependency_overrides.pop(pdf_extraction_service.get_male_extractor, None)

    assert resp.status_code == 200
    assert "ת. לידה: 24.06.2002" in captured["text"]
    assert "כתובת: בני ברק" in captured["text"]


def test_extract_unsupported_file_type_is_415(client, shadchan_id):
    resp = _post_file(client, shadchan_id, "male", "resume.txt", b"some text", "text/plain")

    assert resp.status_code == 415


def test_extract_missing_extension_is_415(client, shadchan_id):
    resp = _post_file(client, shadchan_id, "male", "resume", b"some text", "application/octet-stream")

    assert resp.status_code == 415


def test_extract_empty_file_is_400(client, shadchan_id):
    resp = _post_file(client, shadchan_id, "male", "resume.pdf", b"", "application/pdf")

    assert resp.status_code == 400


def test_extract_corrupt_pdf_is_400(client, shadchan_id):
    resp = _post_file(client, shadchan_id, "male", "resume.pdf", b"this is not a real pdf", "application/pdf")

    assert resp.status_code == 400


def test_extract_corrupt_docx_is_400(client, shadchan_id):
    resp = _post_file(
        client,
        shadchan_id,
        "male",
        "resume.docx",
        b"this is not a real docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    assert resp.status_code == 400
