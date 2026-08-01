from sqlalchemy.orm import Session

from app.models.shadchan import Shadchan
from app.schemas.shadchan import ShadchanCreate


def get_shadchan(db: Session, shadchan_id: int) -> Shadchan | None:
    return db.get(Shadchan, shadchan_id)


def create_shadchan(db: Session, data: ShadchanCreate) -> Shadchan:
    shadchan = Shadchan(name=data.name, phone=data.phone, email=data.email)
    db.add(shadchan)
    db.commit()
    db.refresh(shadchan)
    return shadchan
