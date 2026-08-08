from typing import Callable

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth import require_own_shadchan, verify_firebase_token
from app.core.database import get_db
from app.schemas.candidate import (
    CandidateFilters,
    FemaleCandidateCreate,
    FemaleCandidateRead,
    FemaleCandidateUpdate,
    MaleCandidateCreate,
    MaleCandidateRead,
    MaleCandidateUpdate,
    ShadchanCandidatesRead,
)
from app.schemas.pdf_extraction import FemaleCandidateDraft, MaleCandidateDraft, PdfRowsIn
from app.schemas.shadchan import ShadchanCreate, ShadchanRead
from app.services import candidate_service, pdf_extraction_service, shadchan_service

router = APIRouter(prefix="/api/v1/shadchanim", tags=["shadchanim"])


@router.post("", response_model=ShadchanRead, status_code=status.HTTP_201_CREATED)
def register_shadchan(
    payload: ShadchanCreate, db: Session = Depends(get_db), decoded: dict = Depends(verify_firebase_token)
) -> ShadchanRead:
    return shadchan_service.register_shadchan(db, payload, decoded["uid"])


@router.get("/{shadchan_id}/candidates", response_model=ShadchanCandidatesRead)
def get_candidates(
    shadchan_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    filters: CandidateFilters = Depends(),
    db: Session = Depends(get_db),
    _=Depends(require_own_shadchan),
) -> ShadchanCandidatesRead:
    return candidate_service.get_shadchan_candidates(db, shadchan_id, limit, offset, filters)


@router.post(
    "/{shadchan_id}/male-candidates", response_model=MaleCandidateRead, status_code=status.HTTP_201_CREATED
)
def create_male_candidate(
    shadchan_id: int, payload: MaleCandidateCreate, db: Session = Depends(get_db), _=Depends(require_own_shadchan)
) -> MaleCandidateRead:
    return candidate_service.create_male_candidate(db, shadchan_id, payload)


@router.post(
    "/{shadchan_id}/female-candidates", response_model=FemaleCandidateRead, status_code=status.HTTP_201_CREATED
)
def create_female_candidate(
    shadchan_id: int, payload: FemaleCandidateCreate, db: Session = Depends(get_db), _=Depends(require_own_shadchan)
) -> FemaleCandidateRead:
    return candidate_service.create_female_candidate(db, shadchan_id, payload)


@router.post("/{shadchan_id}/male-candidates/extract", response_model=MaleCandidateDraft)
def extract_male_candidate(
    shadchan_id: int,
    payload: PdfRowsIn,
    _=Depends(require_own_shadchan),
    extract: Callable[[dict], MaleCandidateDraft] = Depends(pdf_extraction_service.get_male_extractor),
) -> MaleCandidateDraft:
    return extract(payload.rows)


@router.post("/{shadchan_id}/female-candidates/extract", response_model=FemaleCandidateDraft)
def extract_female_candidate(
    shadchan_id: int,
    payload: PdfRowsIn,
    _=Depends(require_own_shadchan),
    extract: Callable[[dict], FemaleCandidateDraft] = Depends(pdf_extraction_service.get_female_extractor),
) -> FemaleCandidateDraft:
    return extract(payload.rows)


@router.patch("/{shadchan_id}/male-candidates/{candidate_id}", response_model=MaleCandidateRead)
def update_male_candidate(
    shadchan_id: int,
    candidate_id: int,
    payload: MaleCandidateUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_own_shadchan),
) -> MaleCandidateRead:
    return candidate_service.update_male_candidate(db, shadchan_id, candidate_id, payload)


@router.patch("/{shadchan_id}/female-candidates/{candidate_id}", response_model=FemaleCandidateRead)
def update_female_candidate(
    shadchan_id: int,
    candidate_id: int,
    payload: FemaleCandidateUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_own_shadchan),
) -> FemaleCandidateRead:
    return candidate_service.update_female_candidate(db, shadchan_id, candidate_id, payload)
