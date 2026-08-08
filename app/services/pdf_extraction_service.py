import json
from typing import Callable

import groq
from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.groq_client import get_groq_client
from app.schemas.pdf_extraction import FemaleCandidateDraft, MaleCandidateDraft

_SYSTEM_PROMPT = """\
You are given raw label -> text rows extracted from a Hebrew shidduch resume
PDF. Different shadchanim (matchmakers) phrase the same field differently -
map these rows onto the target JSON schema. Use only information present in
the rows; leave a field null if it isn't present or is unclear. Do not
invent data.

Guidance for reference roles (references[].ref_type):
- "רב בישיבה" / "רב" / "מלמד" / "חברותא" (a rabbi or teacher) -> rabbi_teacher
- "חבר" (a friend) -> friend
- "שכן" or other family-adjacent acquaintances -> family

Each bullet point under a relatives/references section header is a separate
entry - do not merge multiple people into one entry.

Respond with JSON only, matching the provided schema.
"""


def _extract(rows: dict[str, str | list[str]], draft_model: type[BaseModel]) -> BaseModel:
    try:
        response = get_groq_client().chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(rows, ensure_ascii=False)},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": draft_model.__name__,
                    "schema": draft_model.model_json_schema(),
                    # not strict - every field is optional/best-effort, and pydantic
                    # validation below is the real safety net for malformed output
                    "strict": False,
                },
            },
        )
        content = response.choices[0].message.content
        return draft_model.model_validate_json(content)
    except (groq.APIError, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="Candidate extraction failed, please try again"
        ) from exc


def extract_male_candidate(rows: dict[str, str | list[str]]) -> MaleCandidateDraft:
    return _extract(rows, MaleCandidateDraft)


def extract_female_candidate(rows: dict[str, str | list[str]]) -> FemaleCandidateDraft:
    return _extract(rows, FemaleCandidateDraft)


def get_male_extractor() -> Callable[[dict[str, str | list[str]]], MaleCandidateDraft]:
    return extract_male_candidate


def get_female_extractor() -> Callable[[dict[str, str | list[str]]], FemaleCandidateDraft]:
    return extract_female_candidate
