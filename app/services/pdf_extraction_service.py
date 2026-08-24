from typing import Callable

import groq
from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.groq_client import get_groq_client
from app.schemas.pdf_extraction import FemaleCandidateDraft, MaleCandidateDraft

_SYSTEM_PROMPT = """\
You are given raw free text extracted from a Hebrew shidduch resume PDF -
the client did no structuring, so line breaks/spacing may be imperfect
artifacts of PDF text extraction. Different shadchanim (matchmakers) phrase
the same field differently - find each field's label and value within the
text and map it onto the target JSON schema. Use only information present
in the text; leave a field null if it isn't present or is unclear. Do not
invent data.

Every piece of information in the text must end up represented somewhere in
the output - never silently drop any of it. If something doesn't correspond
to any field in the schema (other than notes/relatives/references), append
it to the top-level `notes` field instead, formatted as "label: value" on
its own line, so no information from the resume is lost.

All text values (including notes) must be copied verbatim in the original
Hebrew as it appears in the source text - do not translate, transliterate,
or paraphrase into English or any other language.

Guidance for reference roles (references[].ref_type):
- "רב בישיבה" / "רב" / "מלמד" / "חברותא" (a rabbi or teacher) -> rabbi_teacher
- "חבר" (a friend) -> friend
- "שכן" or other family-adjacent acquaintances -> family

Each bullet point or line under a relatives/references section header is a
separate entry - do not merge multiple people into one entry.

Respond with JSON only, matching the provided schema.
"""


def _extract(text: str, draft_model: type[BaseModel]) -> BaseModel:
    try:
        response = get_groq_client().chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": text},
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


def extract_male_candidate(text: str) -> MaleCandidateDraft:
    return _extract(text, MaleCandidateDraft)


def extract_female_candidate(text: str) -> FemaleCandidateDraft:
    return _extract(text, FemaleCandidateDraft)


def get_male_extractor() -> Callable[[str], MaleCandidateDraft]:
    return extract_male_candidate


def get_female_extractor() -> Callable[[str], FemaleCandidateDraft]:
    return extract_female_candidate
