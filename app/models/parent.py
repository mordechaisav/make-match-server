from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class MaleParents(Base, TimestampMixin):
    __tablename__ = "male_parents"

    id: Mapped[int] = mapped_column(primary_key=True)
    male_candidate_id: Mapped[int] = mapped_column(
        ForeignKey("male_candidates.id"), unique=True, nullable=False
    )
    father_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    mother_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    mother_maiden_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    father_occupation: Mapped[str | None] = mapped_column(String(200), nullable=True)
    mother_occupation: Mapped[str | None] = mapped_column(String(200), nullable=True)

    candidate: Mapped["MaleCandidate"] = relationship(back_populates="parents")


class FemaleParents(Base, TimestampMixin):
    __tablename__ = "female_parents"

    id: Mapped[int] = mapped_column(primary_key=True)
    female_candidate_id: Mapped[int] = mapped_column(
        ForeignKey("female_candidates.id"), unique=True, nullable=False
    )
    father_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    mother_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    mother_maiden_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    father_occupation: Mapped[str | None] = mapped_column(String(200), nullable=True)
    mother_occupation: Mapped[str | None] = mapped_column(String(200), nullable=True)

    candidate: Mapped["FemaleCandidate"] = relationship(back_populates="parents")
