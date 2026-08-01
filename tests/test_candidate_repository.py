import datetime

from sqlalchemy import event

from app.models.candidate import MaleCandidate
from app.models.enums import ReferenceType, RelationType
from app.models.reference import CandidateReference
from app.models.relative import Relative
from app.models.shadchan import Shadchan
from app.repositories import candidate_repository


def _seed_male_candidates_with_relations(db_session, count, siblings_per_candidate, references_per_candidate):
    shadchan = Shadchan(name="R. Test", phone="050-000-0000", email="test@example.com")
    db_session.add(shadchan)
    db_session.flush()

    for i in range(count):
        candidate = MaleCandidate(
            shadchan_id=shadchan.id,
            first_name=f"M{i}",
            last_name="Test",
            dob=datetime.date(2000, 1, 1),
        )
        db_session.add(candidate)
        db_session.flush()

        db_session.add(Relative(male_candidate_id=candidate.id, relation=RelationType.FATHER, name="David"))
        db_session.add(Relative(male_candidate_id=candidate.id, relation=RelationType.MOTHER, name="Sara"))
        for j in range(siblings_per_candidate):
            db_session.add(
                Relative(male_candidate_id=candidate.id, relation=RelationType.SIBLING, name=f"Sib{j}")
            )
        for j in range(references_per_candidate):
            db_session.add(
                CandidateReference(
                    male_candidate_id=candidate.id, ref_type=ReferenceType.FRIEND, name=f"Ref{j}"
                )
            )

    db_session.commit()
    return shadchan.id


def _count_queries(engine, fn):
    queries = []
    listener = lambda *args: queries.append(args[2])  # noqa: E731
    event.listen(engine, "before_cursor_execute", listener)
    try:
        result = fn()
    finally:
        event.remove(engine, "before_cursor_execute", listener)
    return result, queries


def test_get_male_candidates_query_count_is_constant_regardless_of_row_count(db_session, engine):
    shadchan_id = _seed_male_candidates_with_relations(
        db_session, count=5, siblings_per_candidate=3, references_per_candidate=3
    )
    db_session.expire_all()

    candidates, queries = _count_queries(
        engine, lambda: candidate_repository.get_male_candidates(db_session, shadchan_id, limit=50, offset=0)
    )

    assert len(candidates) == 5
    for candidate in candidates:
        # 1 father + 1 mother + 3 siblings, all in the unified relatives list
        assert len(candidate.relatives) == 5
        assert {r.relation for r in candidate.relatives} == {
            RelationType.FATHER, RelationType.MOTHER, RelationType.SIBLING
        }
        assert len(candidate.references) == 3

    # 1 candidates query + 1 selectinload(relatives) + 1 selectinload(references)
    # must not grow with candidate count or nested-row count
    assert len(queries) == 3


def test_get_male_candidates_query_count_does_not_scale_with_more_candidates(db_session, engine):
    shadchan_id = _seed_male_candidates_with_relations(
        db_session, count=20, siblings_per_candidate=2, references_per_candidate=2
    )
    db_session.expire_all()

    candidates, queries = _count_queries(
        engine, lambda: candidate_repository.get_male_candidates(db_session, shadchan_id, limit=50, offset=0)
    )

    assert len(candidates) == 20
    assert len(queries) == 3
