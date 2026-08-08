from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.candidate import FemaleCandidate, MaleCandidate
from app.schemas.candidate import (
    CandidateFilters,
    FemaleCandidateCreate,
    FemaleCandidateUpdate,
    MaleCandidateCreate,
    MaleCandidateUpdate,
)


def _dob_cutoff(years_ago: int) -> date:
    today = date.today()
    try:
        return today.replace(year=today.year - years_ago)
    except ValueError:
        # today is Feb 29 and the target year has no leap day
        return today.replace(month=2, day=28, year=today.year - years_ago)


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _apply_candidate_filters(stmt, model, filters: CandidateFilters | None):
    if filters is None:
        return stmt
    if filters.age_min is not None:
        # at least age_min years old today -> born on/before that cutoff
        stmt = stmt.where(model.dob <= _dob_cutoff(filters.age_min))
    if filters.age_max is not None:
        # at most age_max years old today -> born after the next cutoff
        stmt = stmt.where(model.dob > _dob_cutoff(filters.age_max + 1))
    if filters.height_min is not None:
        stmt = stmt.where(model.height >= filters.height_min)
    if filters.height_max is not None:
        stmt = stmt.where(model.height <= filters.height_max)
    if filters.address:
        stmt = stmt.where(model.address.ilike(f"%{_escape_like(filters.address)}%", escape="\\"))
    return stmt


def _male_candidate_stmt():
    return select(MaleCandidate).options(
        selectinload(MaleCandidate.relatives),
        selectinload(MaleCandidate.references),
    )


def _female_candidate_stmt():
    return select(FemaleCandidate).options(
        selectinload(FemaleCandidate.relatives),
        selectinload(FemaleCandidate.references),
    )


def get_male_candidates(
    db: Session, shadchan_id: int, limit: int, offset: int, filters: CandidateFilters | None = None
) -> list[MaleCandidate]:
    stmt = _male_candidate_stmt().where(MaleCandidate.shadchan_id == shadchan_id)
    stmt = _apply_candidate_filters(stmt, MaleCandidate, filters)
    stmt = stmt.order_by(MaleCandidate.id).limit(limit).offset(offset)
    return list(db.execute(stmt).unique().scalars().all())


def get_female_candidates(
    db: Session, shadchan_id: int, limit: int, offset: int, filters: CandidateFilters | None = None
) -> list[FemaleCandidate]:
    stmt = _female_candidate_stmt().where(FemaleCandidate.shadchan_id == shadchan_id)
    stmt = _apply_candidate_filters(stmt, FemaleCandidate, filters)
    stmt = stmt.order_by(FemaleCandidate.id).limit(limit).offset(offset)
    return list(db.execute(stmt).unique().scalars().all())


def get_male_candidate(db: Session, shadchan_id: int, candidate_id: int) -> MaleCandidate | None:
    stmt = _male_candidate_stmt().where(
        MaleCandidate.id == candidate_id, MaleCandidate.shadchan_id == shadchan_id
    )
    return db.execute(stmt).unique().scalar_one_or_none()


def get_female_candidate(db: Session, shadchan_id: int, candidate_id: int) -> FemaleCandidate | None:
    stmt = _female_candidate_stmt().where(
        FemaleCandidate.id == candidate_id, FemaleCandidate.shadchan_id == shadchan_id
    )
    return db.execute(stmt).unique().scalar_one_or_none()


def create_male_candidate(db: Session, shadchan_id: int, data: MaleCandidateCreate) -> MaleCandidate:
    candidate = MaleCandidate(shadchan_id=shadchan_id, **data.model_dump())
    db.add(candidate)
    db.commit()
    return get_male_candidate(db, shadchan_id, candidate.id)


def create_female_candidate(db: Session, shadchan_id: int, data: FemaleCandidateCreate) -> FemaleCandidate:
    candidate = FemaleCandidate(shadchan_id=shadchan_id, **data.model_dump())
    db.add(candidate)
    db.commit()
    return get_female_candidate(db, shadchan_id, candidate.id)


def update_male_candidate(db: Session, candidate: MaleCandidate, data: MaleCandidateUpdate) -> MaleCandidate:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(candidate, field, value)
    db.commit()
    return get_male_candidate(db, candidate.shadchan_id, candidate.id)


def update_female_candidate(db: Session, candidate: FemaleCandidate, data: FemaleCandidateUpdate) -> FemaleCandidate:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(candidate, field, value)
    db.commit()
    return get_female_candidate(db, candidate.shadchan_id, candidate.id)


def count_male_candidates(db: Session, shadchan_id: int, filters: CandidateFilters | None = None) -> int:
    stmt = select(func.count()).select_from(MaleCandidate).where(MaleCandidate.shadchan_id == shadchan_id)
    stmt = _apply_candidate_filters(stmt, MaleCandidate, filters)
    return db.execute(stmt).scalar_one()


def count_female_candidates(db: Session, shadchan_id: int, filters: CandidateFilters | None = None) -> int:
    stmt = select(func.count()).select_from(FemaleCandidate).where(FemaleCandidate.shadchan_id == shadchan_id)
    stmt = _apply_candidate_filters(stmt, FemaleCandidate, filters)
    return db.execute(stmt).scalar_one()
