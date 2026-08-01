"""Dev-only helper: populate the database with mock data for manual/API testing.

Run with: python -m scripts.seed_data
Safe to re-run - it clears existing rows in the relevant tables first.
"""

import datetime

from app.core.database import SessionLocal
from app.models.candidate import FemaleCandidate, MaleCandidate
from app.models.enums import ReferenceType
from app.models.parent import FemaleParents, MaleParents
from app.models.reference import FemaleReference, MaleReference
from app.models.shadchan import Shadchan
from app.models.sibling import FemaleSibling, MaleSibling


def clear(db):
    for model in (
        MaleReference, FemaleReference,
        MaleSibling, FemaleSibling,
        MaleParents, FemaleParents,
        MaleCandidate, FemaleCandidate,
        Shadchan,
    ):
        db.query(model).delete()
    db.commit()


def seed(db):
    cohen = Shadchan(name="Rebbetzin Cohen", phone="050-111-2222", email="cohen@shadchanim.example")
    katz = Shadchan(name="R. Katz", phone="052-333-4444", email="katz@shadchanim.example")
    db.add_all([cohen, katz])
    db.flush()

    yosef = MaleCandidate(
        shadchan_id=cohen.id, first_name="Yosef", last_name="Levi",
        dob=datetime.date(1998, 1, 12), height=175, address="Bnei Brak",
        talmud_torah="Talmud Torah Chasdei Torah", yeshiva_ketana="Chevron",
        yeshiva_gedola="Ponevezh",
    )
    dovid = MaleCandidate(
        shadchan_id=cohen.id, first_name="Dovid", last_name="Weiss",
        dob=datetime.date(1997, 6, 3), height=180, address="Jerusalem",
        talmud_torah="Talmud Torah Yesodei Hatorah", yeshiva_ketana="Chevron",
        yeshiva_gedola="Mir",
    )
    mendel = MaleCandidate(
        shadchan_id=katz.id, first_name="Mendel", last_name="Braun",
        dob=datetime.date(1999, 3, 21), height=172, address="Modiin Illit",
        talmud_torah="Talmud Torah Modiin Illit",
    )
    db.add_all([yosef, dovid, mendel])

    rivka = FemaleCandidate(
        shadchan_id=cohen.id, first_name="Rivka", last_name="Klein",
        dob=datetime.date(1999, 5, 5), height=163, address="Jerusalem",
        beit_yaakov="Beis Yaakov Yerushalayim", seminar="Bais Yaakov Seminary",
    )
    chaya = FemaleCandidate(
        shadchan_id=cohen.id, first_name="Chaya", last_name="Friedman",
        dob=datetime.date(2000, 11, 30), height=160, address="Bnei Brak",
        beit_yaakov="Beis Yaakov Bnei Brak", seminar="Seminar Bnos Chaya",
        maslul="Machon Lev - Speech Therapy Track",
    )
    db.add_all([rivka, chaya])
    db.flush()

    db.add_all([
        MaleParents(male_candidate_id=yosef.id, father_name="David Levi", mother_name="Sara Levi",
                    father_occupation="Rosh Kollel"),
        MaleParents(male_candidate_id=dovid.id, father_name="Aharon Weiss", mother_name="Rochel Weiss",
                    mother_maiden_name="Stern"),
        MaleParents(male_candidate_id=mendel.id, father_name="Yitzchok Braun", mother_name="Miriam Braun"),
        FemaleParents(female_candidate_id=rivka.id, father_name="Moshe Klein", mother_name="Leah Klein",
                      father_occupation="Sofer"),
        FemaleParents(female_candidate_id=chaya.id, father_name="Shimon Friedman", mother_name="Esther Friedman",
                      mother_maiden_name="Roth"),
    ])

    db.add_all([
        MaleSibling(male_candidate_id=yosef.id, name="Chaim Levi", marital_status="married"),
        MaleSibling(male_candidate_id=yosef.id, name="Berel Levi", marital_status="single"),
        FemaleSibling(female_candidate_id=rivka.id, name="Sury Klein", marital_status="married",
                      details="Married to a talmid in Mir"),
    ])

    db.add_all([
        MaleReference(male_candidate_id=yosef.id, ref_type=ReferenceType.RABBI_TEACHER, name="Rav Katz",
                      role_connection="Rebbi in Ponevezh", phone="03-555-0101"),
        MaleReference(male_candidate_id=dovid.id, ref_type=ReferenceType.FRIEND, name="Shloime Adler",
                      role_connection="Chavrusa"),
        FemaleReference(female_candidate_id=rivka.id, ref_type=ReferenceType.FAMILY, name="Tante Bracha",
                        role_connection="Aunt", phone="02-555-0202"),
    ])

    db.commit()
    return cohen, katz


if __name__ == "__main__":
    db = SessionLocal()
    try:
        clear(db)
        cohen, katz = seed(db)
        print(f"Seeded shadchan '{cohen.name}' (id={cohen.id}) and '{katz.name}' (id={katz.id})")
    finally:
        db.close()
