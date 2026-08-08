from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Shadchan(Base, TimestampMixin):
    __tablename__ = "shadchanim"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False)
    firebase_uid: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)

    male_candidates: Mapped[list["MaleCandidate"]] = relationship(back_populates="shadchan")
    female_candidates: Mapped[list["FemaleCandidate"]] = relationship(back_populates="shadchan")
