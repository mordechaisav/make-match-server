from datetime import date

from sqlalchemy import CheckConstraint, Date, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import RelationType
from app.models.mixins import TimestampMixin


class Relative(Base, TimestampMixin):
    __tablename__ = "relatives"
    __table_args__ = (
        CheckConstraint(
            "(male_candidate_id IS NOT NULL AND female_candidate_id IS NULL) OR "
            "(male_candidate_id IS NULL AND female_candidate_id IS NOT NULL)",
            name="ck_relatives_exactly_one_candidate",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    male_candidate_id: Mapped[int | None] = mapped_column(ForeignKey("male_candidates.id"), nullable=True)
    female_candidate_id: Mapped[int | None] = mapped_column(ForeignKey("female_candidates.id"), nullable=True)
    relation: Mapped[RelationType] = mapped_column(Enum(RelationType, name="relation_type"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    maiden_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(200), nullable=True)
    dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    marital_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    details: Mapped[str | None] = mapped_column(String(500), nullable=True)

    male_candidate: Mapped["MaleCandidate | None"] = relationship(back_populates="relatives")
    female_candidate: Mapped["FemaleCandidate | None"] = relationship(back_populates="relatives")
