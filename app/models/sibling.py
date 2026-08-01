from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class MaleSibling(Base, TimestampMixin):
    __tablename__ = "male_siblings"

    id: Mapped[int] = mapped_column(primary_key=True)
    male_candidate_id: Mapped[int] = mapped_column(ForeignKey("male_candidates.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    marital_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    details: Mapped[str | None] = mapped_column(String(500), nullable=True)

    candidate: Mapped["MaleCandidate"] = relationship(back_populates="siblings")


class FemaleSibling(Base, TimestampMixin):
    __tablename__ = "female_siblings"

    id: Mapped[int] = mapped_column(primary_key=True)
    female_candidate_id: Mapped[int] = mapped_column(ForeignKey("female_candidates.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    marital_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    details: Mapped[str | None] = mapped_column(String(500), nullable=True)

    candidate: Mapped["FemaleCandidate"] = relationship(back_populates="siblings")
