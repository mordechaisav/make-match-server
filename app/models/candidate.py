from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class MaleCandidate(Base, TimestampMixin):
    __tablename__ = "male_candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    shadchan_id: Mapped[int] = mapped_column(ForeignKey("shadchanim.id"), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dob: Mapped[date] = mapped_column(Date, nullable=False)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    picture_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    talmud_torah: Mapped[str | None] = mapped_column(String(200), nullable=True)
    yeshiva_ketana: Mapped[str | None] = mapped_column(String(200), nullable=True)
    yeshiva_gedola: Mapped[str | None] = mapped_column(String(200), nullable=True)

    shadchan: Mapped["Shadchan"] = relationship(back_populates="male_candidates")
    relatives: Mapped[list["Relative"]] = relationship(
        back_populates="male_candidate", cascade="all, delete-orphan"
    )
    references: Mapped[list["CandidateReference"]] = relationship(
        back_populates="male_candidate", cascade="all, delete-orphan"
    )


class FemaleCandidate(Base, TimestampMixin):
    __tablename__ = "female_candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    shadchan_id: Mapped[int] = mapped_column(ForeignKey("shadchanim.id"), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dob: Mapped[date] = mapped_column(Date, nullable=False)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    picture_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    beit_yaakov: Mapped[str | None] = mapped_column(String(200), nullable=True)
    seminar: Mapped[str | None] = mapped_column(String(200), nullable=True)
    maslul: Mapped[str | None] = mapped_column(String(200), nullable=True)

    shadchan: Mapped["Shadchan"] = relationship(back_populates="female_candidates")
    relatives: Mapped[list["Relative"]] = relationship(
        back_populates="female_candidate", cascade="all, delete-orphan"
    )
    references: Mapped[list["CandidateReference"]] = relationship(
        back_populates="female_candidate", cascade="all, delete-orphan"
    )
