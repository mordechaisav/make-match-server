from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories import shadchan_repository
from app.schemas.shadchan import ShadchanCreate, ShadchanRead

_ALREADY_REGISTERED_DETAIL = "This account is already registered as a shadchan"


def register_shadchan(db: Session, data: ShadchanCreate, firebase_uid: str) -> ShadchanRead:
    if shadchan_repository.get_shadchan_by_firebase_uid(db, firebase_uid) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, _ALREADY_REGISTERED_DETAIL)
    try:
        shadchan = shadchan_repository.create_shadchan(db, data, firebase_uid)
    except IntegrityError:
        # concurrent request registered the same firebase_uid between our check and this insert
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, _ALREADY_REGISTERED_DETAIL)
    return ShadchanRead.model_validate(shadchan)
