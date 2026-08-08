from fastapi import Depends, Header, HTTPException, status
from firebase_admin import auth as firebase_auth
from firebase_admin.exceptions import FirebaseError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.firebase import get_firebase_app
from app.models.shadchan import Shadchan
from app.repositories import shadchan_repository


def verify_firebase_token(authorization: str | None = Header(None)) -> dict:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing or malformed Authorization header")

    # resolved outside the try so SDK/credential misconfiguration surfaces as a 500,
    # not a misleading 401 that looks like a client-side auth failure
    app = get_firebase_app()
    try:
        return firebase_auth.verify_id_token(token, app=app)
    except (ValueError, FirebaseError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token") from exc


def get_current_shadchan(
    db: Session = Depends(get_db),
    decoded: dict = Depends(verify_firebase_token),
) -> Shadchan | None:
    return shadchan_repository.get_shadchan_by_firebase_uid(db, decoded["uid"])


def require_own_shadchan(
    shadchan_id: int,
    current: Shadchan | None = Depends(get_current_shadchan),
) -> Shadchan:
    if current is None or current.id != shadchan_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized for this shadchan")
    return current
