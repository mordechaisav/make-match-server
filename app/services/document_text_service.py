import io
from pathlib import Path
from typing import Callable

import docx
from fastapi import HTTPException, UploadFile, status
from pypdf import PdfReader


def _extract_pdf_text(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_docx_text(data: bytes) -> str:
    document = docx.Document(io.BytesIO(data))
    parts = [p.text for p in document.paragraphs if p.text.strip()]
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    parts.append(cell.text)
    return "\n".join(parts)


_EXTRACTORS_BY_EXTENSION: dict[str, Callable[[bytes], str]] = {
    ".pdf": _extract_pdf_text,
    ".docx": _extract_docx_text,
}


def extract_text_from_upload(file: UploadFile) -> str:
    """Read an uploaded resume (.pdf or .docx) and return its raw text.

    Dispatches purely on the filename extension - content_type is set by the
    client and isn't reliable enough to trust for routing to a parser.
    """
    extension = Path(file.filename or "").suffix.lower()
    extractor = _EXTRACTORS_BY_EXTENSION.get(extension)
    if extractor is None:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type - only .pdf and .docx resumes are accepted",
        )

    data = file.file.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")

    try:
        text = extractor(data)
    except Exception as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Could not read the uploaded file - it may be corrupted or password protected",
        ) from exc

    if not text.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Could not extract any text from the uploaded file")
    return text


def get_text_extractor() -> Callable[[UploadFile], str]:
    return extract_text_from_upload
