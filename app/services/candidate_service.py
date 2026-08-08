from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.shadchan import Shadchan
from app.repositories import candidate_repository
from app.schemas.candidate import (
    CandidateFilters,
    FemaleCandidateCreate,
    FemaleCandidateRead,
    FemaleCandidateUpdate,
    MaleCandidateCreate,
    MaleCandidateRead,
    MaleCandidateUpdate,
    PaginationMeta,
    ShadchanCandidatesRead,
)


def _get_shadchan_or_404(db: Session, shadchan_id: int) -> Shadchan:
    shadchan = db.get(Shadchan, shadchan_id)
    if shadchan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shadchan not found")
    return shadchan


def get_shadchan_candidates(
    db: Session, shadchan_id: int, limit: int, offset: int, filters: CandidateFilters | None = None
) -> ShadchanCandidatesRead:
    _get_shadchan_or_404(db, shadchan_id)

    male_candidates = candidate_repository.get_male_candidates(db, shadchan_id, limit, offset, filters)
    female_candidates = candidate_repository.get_female_candidates(db, shadchan_id, limit, offset, filters)
    male_total = candidate_repository.count_male_candidates(db, shadchan_id, filters)
    female_total = candidate_repository.count_female_candidates(db, shadchan_id, filters)

    return ShadchanCandidatesRead(
        shadchan_id=shadchan_id,
        male_candidates=male_candidates,
        female_candidates=female_candidates,
        pagination=PaginationMeta(
            limit=limit,
            offset=offset,
            male_total=male_total,
            female_total=female_total,
        ),
    )


def create_male_candidate(db: Session, shadchan_id: int, data: MaleCandidateCreate) -> MaleCandidateRead:
    _get_shadchan_or_404(db, shadchan_id)
    candidate = candidate_repository.create_male_candidate(db, shadchan_id, data)
    return MaleCandidateRead.model_validate(candidate)


def create_female_candidate(db: Session, shadchan_id: int, data: FemaleCandidateCreate) -> FemaleCandidateRead:
    _get_shadchan_or_404(db, shadchan_id)
    candidate = candidate_repository.create_female_candidate(db, shadchan_id, data)
    return FemaleCandidateRead.model_validate(candidate)


def update_male_candidate(
    db: Session, shadchan_id: int, candidate_id: int, data: MaleCandidateUpdate
) -> MaleCandidateRead:
    _get_shadchan_or_404(db, shadchan_id)
    candidate = candidate_repository.get_male_candidate(db, shadchan_id, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Male candidate not found")
    updated = candidate_repository.update_male_candidate(db, candidate, data)
    return MaleCandidateRead.model_validate(updated)


def update_female_candidate(
    db: Session, shadchan_id: int, candidate_id: int, data: FemaleCandidateUpdate
) -> FemaleCandidateRead:
    _get_shadchan_or_404(db, shadchan_id)
    candidate = candidate_repository.get_female_candidate(db, shadchan_id, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Female candidate not found")
    updated = candidate_repository.update_female_candidate(db, candidate, data)
    return FemaleCandidateRead.model_validate(updated)
