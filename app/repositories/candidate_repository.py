from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.candidate import FemaleCandidate, MaleCandidate
from app.schemas.candidate import (
    FemaleCandidateCreate,
    FemaleCandidateUpdate,
    MaleCandidateCreate,
    MaleCandidateUpdate,
)


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


def get_male_candidates(db: Session, shadchan_id: int, limit: int, offset: int) -> list[MaleCandidate]:
    stmt = (
        _male_candidate_stmt()
        .where(MaleCandidate.shadchan_id == shadchan_id)
        .order_by(MaleCandidate.id)
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).unique().scalars().all())


def get_female_candidates(db: Session, shadchan_id: int, limit: int, offset: int) -> list[FemaleCandidate]:
    stmt = (
        _female_candidate_stmt()
        .where(FemaleCandidate.shadchan_id == shadchan_id)
        .order_by(FemaleCandidate.id)
        .limit(limit)
        .offset(offset)
    )
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


def count_male_candidates(db: Session, shadchan_id: int) -> int:
    stmt = select(func.count()).select_from(MaleCandidate).where(MaleCandidate.shadchan_id == shadchan_id)
    return db.execute(stmt).scalar_one()


def count_female_candidates(db: Session, shadchan_id: int) -> int:
    stmt = select(func.count()).select_from(FemaleCandidate).where(FemaleCandidate.shadchan_id == shadchan_id)
    return db.execute(stmt).scalar_one()
