from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.shadchan import Shadchan
from app.schemas.shadchan import ShadchanCreate, ShadchanUpdate


def get_shadchan(db: Session, shadchan_id: int) -> Shadchan | None:
    return db.get(Shadchan, shadchan_id)


def get_shadchan_by_firebase_uid(db: Session, firebase_uid: str) -> Shadchan | None:
    stmt = select(Shadchan).where(Shadchan.firebase_uid == firebase_uid)
    return db.execute(stmt).scalar_one_or_none()


def create_shadchan(db: Session, data: ShadchanCreate, firebase_uid: str) -> Shadchan:
    shadchan = Shadchan(name=data.name, phone=data.phone, email=data.email, firebase_uid=firebase_uid)
    db.add(shadchan)
    db.commit()
    db.refresh(shadchan)
    return shadchan


def update_shadchan(db: Session, shadchan: Shadchan, data: ShadchanUpdate) -> Shadchan:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(shadchan, field, value)
    db.commit()
    db.refresh(shadchan)
    return shadchan
