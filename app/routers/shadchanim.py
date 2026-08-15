from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_shadchan, require_own_shadchan, verify_firebase_token
from app.core.database import get_db
from app.models.shadchan import Shadchan
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
from app.schemas.image import UploadUrlIn, UploadUrlOut
from app.schemas.pdf_extraction import FemaleCandidateDraft, MaleCandidateDraft, PdfRowsIn
from app.schemas.shadchan import ShadchanCreate, ShadchanRead, ShadchanUpdate
from app.services import candidate_service, image_service, pdf_extraction_service, shadchan_service

router = APIRouter(prefix="/api/v1/shadchanim", tags=["shadchanim"])


@router.post("", response_model=ShadchanRead, status_code=status.HTTP_201_CREATED)
def register_shadchan(
    payload: ShadchanCreate, db: Session = Depends(get_db), decoded: dict = Depends(verify_firebase_token)
) -> ShadchanRead:
    return shadchan_service.register_shadchan(db, payload, decoded["uid"])


@router.get("/me", response_model=ShadchanRead)
def get_my_shadchan(current: Shadchan | None = Depends(get_current_shadchan)) -> ShadchanRead:
    if current is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No shadchan registered for this account")
    return ShadchanRead.model_validate(current)


@router.patch("/{shadchan_id}", response_model=ShadchanRead)
def update_shadchan(
    shadchan_id: int,
    payload: ShadchanUpdate,
    db: Session = Depends(get_db),
    current: Shadchan = Depends(require_own_shadchan),
) -> ShadchanRead:
    return shadchan_service.update_shadchan(db, current, payload)


@router.get("/{shadchan_id}/candidates", response_model=ShadchanCandidatesRead)
def get_candidates(
    shadchan_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    filters: CandidateFilters = Depends(),
    db: Session = Depends(get_db),
    _=Depends(require_own_shadchan),
    read_url_fn: Callable[[str], str] = Depends(image_service.get_read_url_generator),
) -> ShadchanCandidatesRead:
    return candidate_service.get_shadchan_candidates(db, shadchan_id, limit, offset, read_url_fn, filters)


@router.get("/{shadchan_id}/male-candidates/{candidate_id}", response_model=MaleCandidateRead)
def get_male_candidate(
    shadchan_id: int,
    candidate_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_own_shadchan),
    read_url_fn: Callable[[str], str] = Depends(image_service.get_read_url_generator),
) -> MaleCandidateRead:
    return candidate_service.get_male_candidate(db, shadchan_id, candidate_id, read_url_fn)


@router.get("/{shadchan_id}/female-candidates/{candidate_id}", response_model=FemaleCandidateRead)
def get_female_candidate(
    shadchan_id: int,
    candidate_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_own_shadchan),
    read_url_fn: Callable[[str], str] = Depends(image_service.get_read_url_generator),
) -> FemaleCandidateRead:
    return candidate_service.get_female_candidate(db, shadchan_id, candidate_id, read_url_fn)


@router.post("/{shadchan_id}/upload-url", response_model=UploadUrlOut)
def create_upload_url(
    shadchan_id: int,
    payload: UploadUrlIn,
    _=Depends(require_own_shadchan),
    generate: Callable[[int, str], UploadUrlOut] = Depends(image_service.get_upload_url_generator),
) -> UploadUrlOut:
    return generate(shadchan_id, payload.content_type)


@router.post(
    "/{shadchan_id}/male-candidates", response_model=MaleCandidateRead, status_code=status.HTTP_201_CREATED
)
def create_male_candidate(
    shadchan_id: int,
    payload: MaleCandidateCreate,
    db: Session = Depends(get_db),
    _=Depends(require_own_shadchan),
    exists_checker: Callable[[str], bool] = Depends(image_service.get_object_checker),
    read_url_fn: Callable[[str], str] = Depends(image_service.get_read_url_generator),
) -> MaleCandidateRead:
    return candidate_service.create_male_candidate(db, shadchan_id, payload, exists_checker, read_url_fn)


@router.post(
    "/{shadchan_id}/female-candidates", response_model=FemaleCandidateRead, status_code=status.HTTP_201_CREATED
)
def create_female_candidate(
    shadchan_id: int,
    payload: FemaleCandidateCreate,
    db: Session = Depends(get_db),
    _=Depends(require_own_shadchan),
    exists_checker: Callable[[str], bool] = Depends(image_service.get_object_checker),
    read_url_fn: Callable[[str], str] = Depends(image_service.get_read_url_generator),
) -> FemaleCandidateRead:
    return candidate_service.create_female_candidate(db, shadchan_id, payload, exists_checker, read_url_fn)


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
    exists_checker: Callable[[str], bool] = Depends(image_service.get_object_checker),
    read_url_fn: Callable[[str], str] = Depends(image_service.get_read_url_generator),
) -> MaleCandidateRead:
    return candidate_service.update_male_candidate(
        db, shadchan_id, candidate_id, payload, exists_checker, read_url_fn
    )


@router.patch("/{shadchan_id}/female-candidates/{candidate_id}", response_model=FemaleCandidateRead)
def update_female_candidate(
    shadchan_id: int,
    candidate_id: int,
    payload: FemaleCandidateUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_own_shadchan),
    exists_checker: Callable[[str], bool] = Depends(image_service.get_object_checker),
    read_url_fn: Callable[[str], str] = Depends(image_service.get_read_url_generator),
) -> FemaleCandidateRead:
    return candidate_service.update_female_candidate(
        db, shadchan_id, candidate_id, payload, exists_checker, read_url_fn
    )
