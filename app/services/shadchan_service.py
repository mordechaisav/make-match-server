from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.shadchan import Shadchan
from app.repositories import shadchan_repository
from app.schemas.shadchan import ShadchanCreate, ShadchanRead, ShadchanUpdate

_ALREADY_REGISTERED_DETAIL = "This account is already registered as a shadchan"


def _already_registered_detail(existing) -> dict:
    return {"message": _ALREADY_REGISTERED_DETAIL, "shadchan": ShadchanRead.model_validate(existing).model_dump(mode="json")}


def register_shadchan(db: Session, data: ShadchanCreate, firebase_uid: str) -> ShadchanRead:
    existing = shadchan_repository.get_shadchan_by_firebase_uid(db, firebase_uid)
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, _already_registered_detail(existing))
    try:
        shadchan = shadchan_repository.create_shadchan(db, data, firebase_uid)
    except IntegrityError:
        # concurrent request registered the same firebase_uid between our check and this insert
        db.rollback()
        existing = shadchan_repository.get_shadchan_by_firebase_uid(db, firebase_uid)
        raise HTTPException(status.HTTP_409_CONFLICT, _already_registered_detail(existing))
    return ShadchanRead.model_validate(shadchan)


def update_shadchan(db: Session, shadchan: Shadchan, data: ShadchanUpdate) -> ShadchanRead:
    updated = shadchan_repository.update_shadchan(db, shadchan, data)
    return ShadchanRead.model_validate(updated)
