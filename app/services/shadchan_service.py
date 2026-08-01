from sqlalchemy.orm import Session

from app.repositories import shadchan_repository
from app.schemas.shadchan import ShadchanCreate, ShadchanRead


def register_shadchan(db: Session, data: ShadchanCreate) -> ShadchanRead:
    shadchan = shadchan_repository.create_shadchan(db, data)
    return ShadchanRead.model_validate(shadchan)
