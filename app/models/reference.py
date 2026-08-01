from sqlalchemy import CheckConstraint, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ReferenceType
from app.models.mixins import TimestampMixin


class CandidateReference(Base, TimestampMixin):
    # named candidate_references, not references - REFERENCES is a reserved SQL keyword
    __tablename__ = "candidate_references"
    __table_args__ = (
        CheckConstraint(
            "(male_candidate_id IS NOT NULL AND female_candidate_id IS NULL) OR "
            "(male_candidate_id IS NULL AND female_candidate_id IS NOT NULL)",
            name="ck_candidate_references_exactly_one_candidate",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    male_candidate_id: Mapped[int | None] = mapped_column(ForeignKey("male_candidates.id"), nullable=True)
    female_candidate_id: Mapped[int | None] = mapped_column(ForeignKey("female_candidates.id"), nullable=True)
    ref_type: Mapped[ReferenceType] = mapped_column(Enum(ReferenceType, name="reference_type"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    role_connection: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    details: Mapped[str | None] = mapped_column(String(500), nullable=True)

    male_candidate: Mapped["MaleCandidate | None"] = relationship(back_populates="references")
    female_candidate: Mapped["FemaleCandidate | None"] = relationship(back_populates="references")
