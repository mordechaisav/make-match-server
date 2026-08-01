from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ReferenceType
from app.models.mixins import TimestampMixin


class MaleReference(Base, TimestampMixin):
    __tablename__ = "male_references"

    id: Mapped[int] = mapped_column(primary_key=True)
    male_candidate_id: Mapped[int] = mapped_column(ForeignKey("male_candidates.id"), nullable=False)
    ref_type: Mapped[ReferenceType] = mapped_column(Enum(ReferenceType, name="reference_type"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    role_connection: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    details: Mapped[str | None] = mapped_column(String(500), nullable=True)

    candidate: Mapped["MaleCandidate"] = relationship(back_populates="references")


class FemaleReference(Base, TimestampMixin):
    __tablename__ = "female_references"

    id: Mapped[int] = mapped_column(primary_key=True)
    female_candidate_id: Mapped[int] = mapped_column(ForeignKey("female_candidates.id"), nullable=False)
    ref_type: Mapped[ReferenceType] = mapped_column(Enum(ReferenceType, name="reference_type"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    role_connection: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    details: Mapped[str | None] = mapped_column(String(500), nullable=True)

    candidate: Mapped["FemaleCandidate"] = relationship(back_populates="references")
