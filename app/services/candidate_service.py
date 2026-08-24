from typing import Callable

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


def _check_picture_exists(picture_url: str | None, exists_checker: Callable[[str], bool]) -> None:
    if picture_url and not exists_checker(picture_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded image not found, please upload it again"
        )


def _resolve_picture(candidate_read, read_url_fn: Callable[[str], str]):
    if candidate_read.picture_url:
        candidate_read.picture_url = read_url_fn(candidate_read.picture_url)
    return candidate_read


def get_shadchan_candidates(
    db: Session,
    shadchan_id: int,
    limit: int,
    offset: int,
    read_url_fn: Callable[[str], str],
    filters: CandidateFilters | None = None,
) -> ShadchanCandidatesRead:
    _get_shadchan_or_404(db, shadchan_id)

    male_candidates = candidate_repository.get_male_candidates(db, shadchan_id, limit, offset, filters)
    female_candidates = candidate_repository.get_female_candidates(db, shadchan_id, limit, offset, filters)
    male_total = candidate_repository.count_male_candidates(db, shadchan_id, filters)
    female_total = candidate_repository.count_female_candidates(db, shadchan_id, filters)

    return ShadchanCandidatesRead(
        shadchan_id=shadchan_id,
        male_candidates=[
            _resolve_picture(MaleCandidateRead.model_validate(c), read_url_fn) for c in male_candidates
        ],
        female_candidates=[
            _resolve_picture(FemaleCandidateRead.model_validate(c), read_url_fn) for c in female_candidates
        ],
        pagination=PaginationMeta(
            limit=limit,
            offset=offset,
            male_total=male_total,
            female_total=female_total,
        ),
    )


def get_male_candidate(
    db: Session, shadchan_id: int, candidate_id: int, read_url_fn: Callable[[str], str]
) -> MaleCandidateRead:
    _get_shadchan_or_404(db, shadchan_id)
    candidate = candidate_repository.get_male_candidate(db, shadchan_id, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Male candidate not found")
    return _resolve_picture(MaleCandidateRead.model_validate(candidate), read_url_fn)


def get_female_candidate(
    db: Session, shadchan_id: int, candidate_id: int, read_url_fn: Callable[[str], str]
) -> FemaleCandidateRead:
    _get_shadchan_or_404(db, shadchan_id)
    candidate = candidate_repository.get_female_candidate(db, shadchan_id, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Female candidate not found")
    return _resolve_picture(FemaleCandidateRead.model_validate(candidate), read_url_fn)


def delete_male_candidate(
    db: Session, shadchan_id: int, candidate_id: int, delete_object_fn: Callable[[str], None]
) -> None:
    _get_shadchan_or_404(db, shadchan_id)
    candidate = candidate_repository.get_male_candidate(db, shadchan_id, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Male candidate not found")
    picture_url = candidate.picture_url
    candidate_repository.delete_male_candidate(db, candidate)
    if picture_url:
        delete_object_fn(picture_url)


def delete_female_candidate(
    db: Session, shadchan_id: int, candidate_id: int, delete_object_fn: Callable[[str], None]
) -> None:
    _get_shadchan_or_404(db, shadchan_id)
    candidate = candidate_repository.get_female_candidate(db, shadchan_id, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Female candidate not found")
    picture_url = candidate.picture_url
    candidate_repository.delete_female_candidate(db, candidate)
    if picture_url:
        delete_object_fn(picture_url)


def create_male_candidate(
    db: Session,
    shadchan_id: int,
    data: MaleCandidateCreate,
    exists_checker: Callable[[str], bool],
    read_url_fn: Callable[[str], str],
) -> MaleCandidateRead:
    _get_shadchan_or_404(db, shadchan_id)
    _check_picture_exists(data.picture_url, exists_checker)
    candidate = candidate_repository.create_male_candidate(db, shadchan_id, data)
    return _resolve_picture(MaleCandidateRead.model_validate(candidate), read_url_fn)


def create_female_candidate(
    db: Session,
    shadchan_id: int,
    data: FemaleCandidateCreate,
    exists_checker: Callable[[str], bool],
    read_url_fn: Callable[[str], str],
) -> FemaleCandidateRead:
    _get_shadchan_or_404(db, shadchan_id)
    _check_picture_exists(data.picture_url, exists_checker)
    candidate = candidate_repository.create_female_candidate(db, shadchan_id, data)
    return _resolve_picture(FemaleCandidateRead.model_validate(candidate), read_url_fn)


def update_male_candidate(
    db: Session,
    shadchan_id: int,
    candidate_id: int,
    data: MaleCandidateUpdate,
    exists_checker: Callable[[str], bool],
    read_url_fn: Callable[[str], str],
) -> MaleCandidateRead:
    _get_shadchan_or_404(db, shadchan_id)
    candidate = candidate_repository.get_male_candidate(db, shadchan_id, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Male candidate not found")
    _check_picture_exists(data.picture_url, exists_checker)
    updated = candidate_repository.update_male_candidate(db, candidate, data)
    return _resolve_picture(MaleCandidateRead.model_validate(updated), read_url_fn)


def update_female_candidate(
    db: Session,
    shadchan_id: int,
    candidate_id: int,
    data: FemaleCandidateUpdate,
    exists_checker: Callable[[str], bool],
    read_url_fn: Callable[[str], str],
) -> FemaleCandidateRead:
    _get_shadchan_or_404(db, shadchan_id)
    candidate = candidate_repository.get_female_candidate(db, shadchan_id, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Female candidate not found")
    _check_picture_exists(data.picture_url, exists_checker)
    updated = candidate_repository.update_female_candidate(db, candidate, data)
    return _resolve_picture(FemaleCandidateRead.model_validate(updated), read_url_fn)
