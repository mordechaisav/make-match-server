from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ReferenceType


class ParentsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    father_name: str | None
    mother_name: str | None
    mother_maiden_name: str | None
    father_occupation: str | None
    mother_occupation: str | None


class SiblingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    dob: date | None
    marital_status: str | None
    details: str | None


class ReferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ref_type: ReferenceType
    name: str
    role_connection: str | None
    phone: str | None
    details: str | None


class MaleCandidateCreate(BaseModel):
    first_name: str
    last_name: str
    dob: date
    height: int | None = None
    address: str | None = None
    talmud_torah: str | None = None
    yeshiva_ketana: str | None = None
    yeshiva_gedola: str | None = None


class MaleCandidateUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    dob: date | None = None
    height: int | None = None
    address: str | None = None
    talmud_torah: str | None = None
    yeshiva_ketana: str | None = None
    yeshiva_gedola: str | None = None


class FemaleCandidateCreate(BaseModel):
    first_name: str
    last_name: str
    dob: date
    height: int | None = None
    address: str | None = None
    beit_yaakov: str | None = None
    seminar: str | None = None
    maslul: str | None = None


class FemaleCandidateUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    dob: date | None = None
    height: int | None = None
    address: str | None = None
    beit_yaakov: str | None = None
    seminar: str | None = None
    maslul: str | None = None


class MaleCandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shadchan_id: int
    first_name: str
    last_name: str
    dob: date
    height: int | None
    address: str | None
    created_at: datetime
    updated_at: datetime
    talmud_torah: str | None
    yeshiva_ketana: str | None
    yeshiva_gedola: str | None
    parents: ParentsRead | None
    siblings: list[SiblingRead]
    references: list[ReferenceRead]


class FemaleCandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shadchan_id: int
    first_name: str
    last_name: str
    dob: date
    height: int | None
    address: str | None
    created_at: datetime
    updated_at: datetime
    beit_yaakov: str | None
    seminar: str | None
    maslul: str | None
    parents: ParentsRead | None
    siblings: list[SiblingRead]
    references: list[ReferenceRead]


class PaginationMeta(BaseModel):
    limit: int
    offset: int
    male_total: int
    female_total: int


class ShadchanCandidatesRead(BaseModel):
    shadchan_id: int
    male_candidates: list[MaleCandidateRead]
    female_candidates: list[FemaleCandidateRead]
    pagination: PaginationMeta
