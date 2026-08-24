from datetime import date

from pydantic import BaseModel, Field

from app.models.enums import ReferenceType, RelationType


class RelativeDraft(BaseModel):
    relation: RelationType | None = None
    name: str | None = None
    maiden_name: str | None = None
    occupation: str | None = None
    dob: date | None = None
    marital_status: str | None = None
    details: str | None = None


class ReferenceDraft(BaseModel):
    ref_type: ReferenceType | None = None
    name: str | None = None
    role_connection: str | None = None
    phone: str | None = None
    details: str | None = None


class MaleCandidateDraft(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    dob: date | None = None
    height: int | None = None
    address: str | None = None
    talmud_torah: str | None = None
    yeshiva_ketana: str | None = None
    yeshiva_gedola: str | None = None
    notes: str | None = None
    relatives: list[RelativeDraft] = Field(default_factory=list)
    references: list[ReferenceDraft] = Field(default_factory=list)


class FemaleCandidateDraft(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    dob: date | None = None
    height: int | None = None
    address: str | None = None
    beit_yaakov: str | None = None
    seminar: str | None = None
    maslul: str | None = None
    notes: str | None = None
    relatives: list[RelativeDraft] = Field(default_factory=list)
    references: list[ReferenceDraft] = Field(default_factory=list)
