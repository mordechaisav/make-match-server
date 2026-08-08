from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ReferenceType, RelationType


class CandidateFilters(BaseModel):
    """Optional search filters shared by male and female candidate listing.

    Every field defaults to None (no filter). Add new filters here as
    additional optional fields - the repository only applies the ones
    that are set.
    """

    age_min: int | None = Field(default=None, ge=0, le=150)
    age_max: int | None = Field(default=None, ge=0, le=150)
    height_min: int | None = Field(default=None, ge=0)
    height_max: int | None = Field(default=None, ge=0)
    address: str | None = None


class RelativeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    relation: RelationType
    name: str
    maiden_name: str | None
    occupation: str | None
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


class RelativeCreate(BaseModel):
    relation: RelationType
    name: str
    maiden_name: str | None = None
    occupation: str | None = None
    dob: date | None = None
    marital_status: str | None = None
    details: str | None = None


class ReferenceCreate(BaseModel):
    ref_type: ReferenceType
    name: str
    role_connection: str | None = None
    phone: str | None = None
    details: str | None = None


class MaleCandidateCreate(BaseModel):
    first_name: str
    last_name: str
    dob: date
    height: int | None = None
    address: str | None = None
    picture_url: str | None = None
    talmud_torah: str | None = None
    yeshiva_ketana: str | None = None
    yeshiva_gedola: str | None = None
    relatives: list[RelativeCreate] = Field(default_factory=list)
    references: list[ReferenceCreate] = Field(default_factory=list)


class MaleCandidateUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    dob: date | None = None
    height: int | None = None
    address: str | None = None
    picture_url: str | None = None
    talmud_torah: str | None = None
    yeshiva_ketana: str | None = None
    yeshiva_gedola: str | None = None


class FemaleCandidateCreate(BaseModel):
    first_name: str
    last_name: str
    dob: date
    height: int | None = None
    address: str | None = None
    picture_url: str | None = None
    beit_yaakov: str | None = None
    seminar: str | None = None
    maslul: str | None = None
    relatives: list[RelativeCreate] = Field(default_factory=list)
    references: list[ReferenceCreate] = Field(default_factory=list)


class FemaleCandidateUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    dob: date | None = None
    height: int | None = None
    address: str | None = None
    picture_url: str | None = None
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
    picture_url: str | None
    created_at: datetime
    updated_at: datetime
    talmud_torah: str | None
    yeshiva_ketana: str | None
    yeshiva_gedola: str | None
    relatives: list[RelativeRead]
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
    picture_url: str | None
    created_at: datetime
    updated_at: datetime
    beit_yaakov: str | None
    seminar: str | None
    maslul: str | None
    relatives: list[RelativeRead]
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
