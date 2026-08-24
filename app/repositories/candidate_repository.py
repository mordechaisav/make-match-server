from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.candidate import FemaleCandidate, MaleCandidate
from app.models.reference import CandidateReference
from app.models.relative import Relative
from app.schemas.candidate import (
    CandidateFilters,
    CandidateSort,
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
    if filters.name:
        pattern = f"%{_escape_like(filters.name)}%"
        stmt = stmt.where(
            or_(model.first_name.ilike(pattern, escape="\\"), model.last_name.ilike(pattern, escape="\\"))
        )
    if filters.favourites_only:
        stmt = stmt.where(model.is_favourite.is_(True))
    return stmt


def _apply_sort(stmt, model, sort: CandidateSort):
    # id is a monotonically increasing tiebreaker for equal-timestamp rows (e.g. two
    # candidates created in the same second); its direction is matched to the primary
    # sort's so ties still resolve in a sensible (not reversed) order.
    order = {
        CandidateSort.created_desc: (model.created_at.desc(), model.id.desc()),
        CandidateSort.created_asc: (model.created_at.asc(), model.id.asc()),
        CandidateSort.age_asc: (model.dob.desc(), model.id.asc()),  # youngest first = latest dob
        CandidateSort.age_desc: (model.dob.asc(), model.id.asc()),  # oldest first = earliest dob
        CandidateSort.name_asc: (model.last_name.asc(), model.first_name.asc(), model.id.asc()),
        CandidateSort.name_desc: (model.last_name.desc(), model.first_name.desc(), model.id.asc()),
    }[sort]
    return stmt.order_by(*order)


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
    sort = filters.sort if filters else CandidateSort.created_desc
    stmt = _apply_sort(stmt, MaleCandidate, sort).limit(limit).offset(offset)
    return list(db.execute(stmt).unique().scalars().all())


def get_female_candidates(
    db: Session, shadchan_id: int, limit: int, offset: int, filters: CandidateFilters | None = None
) -> list[FemaleCandidate]:
    stmt = _female_candidate_stmt().where(FemaleCandidate.shadchan_id == shadchan_id)
    stmt = _apply_candidate_filters(stmt, FemaleCandidate, filters)
    sort = filters.sort if filters else CandidateSort.created_desc
    stmt = _apply_sort(stmt, FemaleCandidate, sort).limit(limit).offset(offset)
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
    payload = data.model_dump(exclude={"relatives", "references"})
    candidate = MaleCandidate(shadchan_id=shadchan_id, **payload)
    candidate.relatives = [Relative(**r.model_dump()) for r in data.relatives]
    candidate.references = [CandidateReference(**r.model_dump()) for r in data.references]
    db.add(candidate)
    db.commit()
    return get_male_candidate(db, shadchan_id, candidate.id)


def create_female_candidate(db: Session, shadchan_id: int, data: FemaleCandidateCreate) -> FemaleCandidate:
    payload = data.model_dump(exclude={"relatives", "references"})
    candidate = FemaleCandidate(shadchan_id=shadchan_id, **payload)
    candidate.relatives = [Relative(**r.model_dump()) for r in data.relatives]
    candidate.references = [CandidateReference(**r.model_dump()) for r in data.references]
    db.add(candidate)
    db.commit()
    return get_female_candidate(db, shadchan_id, candidate.id)


def update_male_candidate(db: Session, candidate: MaleCandidate, data: MaleCandidateUpdate) -> MaleCandidate:
    updates = data.model_dump(exclude_unset=True, exclude={"relatives", "references"})
    for field, value in updates.items():
        setattr(candidate, field, value)
    if data.relatives is not None:
        candidate.relatives = [Relative(**r.model_dump()) for r in data.relatives]
    if data.references is not None:
        candidate.references = [CandidateReference(**r.model_dump()) for r in data.references]
    db.commit()
    return get_male_candidate(db, candidate.shadchan_id, candidate.id)


def update_female_candidate(db: Session, candidate: FemaleCandidate, data: FemaleCandidateUpdate) -> FemaleCandidate:
    updates = data.model_dump(exclude_unset=True, exclude={"relatives", "references"})
    for field, value in updates.items():
        setattr(candidate, field, value)
    if data.relatives is not None:
        candidate.relatives = [Relative(**r.model_dump()) for r in data.relatives]
    if data.references is not None:
        candidate.references = [CandidateReference(**r.model_dump()) for r in data.references]
    db.commit()
    return get_female_candidate(db, candidate.shadchan_id, candidate.id)


def delete_male_candidate(db: Session, candidate: MaleCandidate) -> None:
    db.delete(candidate)
    db.commit()


def delete_female_candidate(db: Session, candidate: FemaleCandidate) -> None:
    db.delete(candidate)
    db.commit()


def count_male_candidates(db: Session, shadchan_id: int, filters: CandidateFilters | None = None) -> int:
    stmt = select(func.count()).select_from(MaleCandidate).where(MaleCandidate.shadchan_id == shadchan_id)
    stmt = _apply_candidate_filters(stmt, MaleCandidate, filters)
    return db.execute(stmt).scalar_one()


def count_female_candidates(db: Session, shadchan_id: int, filters: CandidateFilters | None = None) -> int:
    stmt = select(func.count()).select_from(FemaleCandidate).where(FemaleCandidate.shadchan_id == shadchan_id)
    stmt = _apply_candidate_filters(stmt, FemaleCandidate, filters)
    return db.execute(stmt).scalar_one()
