# Shadchan Server — Architecture

Status: decisions finalized, implemented in `app/`.

## 1. Stack

- FastAPI (API layer)
- SQLAlchemy 2.x ORM (models + query layer)
- PostgreSQL (storage)
- Pydantic v2 (request/response schemas)
- Alembic (migrations) — initialized, initial migration generated and
  applied. `alembic/env.py` reads the DB URL from `app.core.config.settings`
  (not `alembic.ini`) so it always targets the same database as the app.
  `app.core.database.init_db()` (`create_all`) still exists as a quick dev
  shortcut but migrations are now the source of truth for schema changes.

## 2. Final decisions

1. **Gender strategy — strict separation.** Every table that hangs off a
   candidate is duplicated per gender: `male_candidates`/`female_candidates`,
   `male_parents`/`female_parents`, `male_siblings`/`female_siblings`,
   `male_references`/`female_references`. Each FK is single-parent and
   non-nullable — no shared/dual-FK tables anywhere. A male and female
   resume never touch the same row.
2. **Education — flattened onto the candidate row, no separate table.**
   `male_candidates` has `talmud_torah`, `yeshiva_ketana`, `yeshiva_gedola`
   (each a nullable institution-name string); `female_candidates` has
   `beit_yaakov`, `seminar`, `maslul`. One column per progression stage,
   holding the institution name for that stage — the stage itself is
   implied by which column is filled in, not by a `type` value. This
   replaced an earlier `male_education`/`female_education` 1:N design;
   the tradeoff is a candidate can now only record one institution per
   stage (no history of e.g. two different yeshiva ketanas).
3. **Parents cardinality — 1:1.** `male_parents.male_candidate_id` and
   `female_parents.female_candidate_id` are `UNIQUE` FKs, one parents row per
   candidate.
4. **Timestamps** — `created_at` / `updated_at` on every table, via a shared
   `TimestampMixin` (`app/models/mixins.py`).
5. **Pagination** — `GET /api/v1/shadchanim/{shadchan_id}/candidates` takes
   `limit` (default 50, max 200) and `offset` (default 0) query params,
   applied independently to the male and female lists, with per-list totals
   in the response so a client can page each side separately.

## 3. Entity-relationship diagram

```mermaid
erDiagram
    SHADCHANIM ||--o{ MALE_CANDIDATES : registers
    SHADCHANIM ||--o{ FEMALE_CANDIDATES : registers

    MALE_CANDIDATES ||--o| MALE_PARENTS : has
    MALE_CANDIDATES ||--o{ MALE_SIBLINGS : has
    MALE_CANDIDATES ||--o{ MALE_REFERENCES : has

    FEMALE_CANDIDATES ||--o| FEMALE_PARENTS : has
    FEMALE_CANDIDATES ||--o{ FEMALE_SIBLINGS : has
    FEMALE_CANDIDATES ||--o{ FEMALE_REFERENCES : has

    SHADCHANIM {
        int id PK
        string name
        string phone
        string email
        datetime created_at
        datetime updated_at
    }
    MALE_CANDIDATES {
        int id PK
        int shadchan_id FK
        string first_name
        string last_name
        date dob
        int height
        string address
        string talmud_torah "institution name, nullable"
        string yeshiva_ketana "institution name, nullable"
        string yeshiva_gedola "institution name, nullable"
        datetime created_at
        datetime updated_at
    }
    FEMALE_CANDIDATES {
        int id PK
        int shadchan_id FK
        string first_name
        string last_name
        date dob
        int height
        string address
        string beit_yaakov "institution name, nullable"
        string seminar "institution name, nullable"
        string maslul "institution name, nullable"
        datetime created_at
        datetime updated_at
    }
    MALE_PARENTS {
        int id PK
        int male_candidate_id FK "unique"
        string father_name
        string mother_name
        string mother_maiden_name
        string father_occupation
        string mother_occupation
        datetime created_at
        datetime updated_at
    }
    FEMALE_PARENTS {
        int id PK
        int female_candidate_id FK "unique"
        string father_name
        string mother_name
        string mother_maiden_name
        string father_occupation
        string mother_occupation
        datetime created_at
        datetime updated_at
    }
    MALE_SIBLINGS {
        int id PK
        int male_candidate_id FK
        string name
        date dob
        string marital_status
        string details
        datetime created_at
        datetime updated_at
    }
    FEMALE_SIBLINGS {
        int id PK
        int female_candidate_id FK
        string name
        date dob
        string marital_status
        string details
        datetime created_at
        datetime updated_at
    }
    MALE_REFERENCES {
        int id PK
        int male_candidate_id FK
        enum ref_type "rabbi_teacher | friend | family"
        string name
        string role_connection
        string phone
        string details
        datetime created_at
        datetime updated_at
    }
    FEMALE_REFERENCES {
        int id PK
        int female_candidate_id FK
        enum ref_type "rabbi_teacher | friend | family"
        string name
        string role_connection
        string phone
        string details
        datetime created_at
        datetime updated_at
    }
```

`marital_status` on siblings is kept as a plain string, not an enum — the
plan didn't specify its value set, so constraining it would be a guess.

## 4. Layered structure

```
app/
  main.py                # FastAPI() instance, router registration
  core/
    config.py              # Settings (DATABASE_URL via env / .env)
    database.py             # engine, SessionLocal, Base, get_db, init_db
  models/                 # SQLAlchemy ORM
    mixins.py               # TimestampMixin
    enums.py                 # ReferenceType
    shadchan.py
    candidate.py              # MaleCandidate, FemaleCandidate (incl. flattened education columns)
    parent.py                 # MaleParents, FemaleParents
    sibling.py                 # MaleSibling, FemaleSibling
    reference.py               # MaleReference, FemaleReference
  schemas/                # Pydantic response models
    candidate.py
  repositories/           # Query layer - owns eager-loading strategy
    candidate_repository.py
  services/               # Business logic between routers and repositories
    candidate_service.py
  routers/
    shadchanim.py
scripts/
  create_tables.py        # dev-only: Base.metadata.create_all()
tests/
```

Routers depend on services, services depend on repositories, repositories
depend on models. `joinedload`/`selectinload` calls live only in
`repositories/`.

## 5. API contract

### POST /api/v1/shadchanim — register_shadchan

Creates a shadchan. Named `register_shadchan` rather than the generic
`create_shadchan` — matches what the operation represents domain-wise.

Body: `{ "name": str, "phone": str, "email": str }` → 201, full `ShadchanRead`
(includes `id`, `created_at`, `updated_at`).

### POST /api/v1/shadchanim/{shadchan_id}/male-candidates
### POST /api/v1/shadchanim/{shadchan_id}/female-candidates

Create a candidate under a shadchan. Split by gender (rather than one route
with a gender field) because the male/female bodies already diverge — the
education columns differ, and this mirrors the underlying table split.
404 if `shadchan_id` doesn't exist. 201 on success, returns the full
`MaleCandidateRead`/`FemaleCandidateRead` shape (parents `null`, siblings/
references `[]` on a fresh candidate).

Body (male): `first_name`, `last_name`, `dob` required; `height`, `address`,
`talmud_torah`, `yeshiva_ketana`, `yeshiva_gedola` optional.
Body (female): same required fields; optional `height`, `address`,
`beit_yaakov`, `seminar`, `maslul`.

### PATCH /api/v1/shadchanim/{shadchan_id}/male-candidates/{candidate_id}
### PATCH /api/v1/shadchanim/{shadchan_id}/female-candidates/{candidate_id}

Partial update — only fields present in the request body are changed
(`exclude_unset`, not "set to null if omitted"). 404 if the shadchan doesn't
exist, or if the candidate doesn't exist *for that shadchan specifically*
(a candidate ID that belongs to a different shadchan 404s here too — the
`shadchan_id` in the path scopes the lookup, not just a sanity check).

### GET /api/v1/shadchanim/{shadchan_id}/candidates

Query params: `limit` (int, default 50, max 200), `offset` (int, default 0).
404 if the shadchan doesn't exist.

```json
{
  "shadchan_id": 1,
  "male_candidates": [
    {
      "id": 1, "shadchan_id": 1, "first_name": "...", "last_name": "...",
      "dob": "...", "height": 0, "address": "...",
      "created_at": "...", "updated_at": "...",
      "talmud_torah": "...", "yeshiva_ketana": "...", "yeshiva_gedola": "...",
      "parents": { "father_name": "...", "mother_name": "..." },
      "siblings": [ { "name": "...", "marital_status": "..." } ],
      "references": [ { "ref_type": "rabbi_teacher", "name": "..." } ]
    }
  ],
  "female_candidates": [ "..." ],
  "pagination": { "limit": 50, "offset": 0, "male_total": 3, "female_total": 5 }
}
```

**Eager-loading strategy** (`app/repositories/candidate_repository.py`):
`joinedload` for the 1:1 `parents` relationship (single JOIN, no row
multiplication), `selectinload` for the 1:N `siblings`/`references`
collections. Using `joinedload` on two simultaneous one-to-many collections
would multiply the primary row by the product of each collection's size (a
Cartesian join) — correct once deduplicated with `.unique()`, but wastes
bandwidth on any candidate with more than a couple of siblings/references.
`selectinload` issues one extra `SELECT ... WHERE id IN (...)` per
collection instead — still exactly O(1) queries per collection (not O(n)
per candidate), so N+1 is avoided either way; this just avoids the
multiplication too. Education needs no eager-loading strategy at all now —
it's plain columns on the candidate row, included for free. Male and female
results are two separate queries (two separate tables), merged in the
service layer.

## 6. Remaining follow-ups (not blocking, not decided here)

- [ ] Auth/authorization on the shadchanim endpoints (none implemented).
- [ ] `marital_status` value set, if the product wants it constrained later.

## 7. Local Postgres (docker-compose)

`docker-compose.yml` at the repo root runs Postgres 16, credentials matching
`.env.example` (`postgresql+psycopg2://postgres:postgres@localhost:5432/shadchan`),
data persisted in a named volume. Start it with `docker compose up -d`.

Migrations: `alembic upgrade head` (applies `alembic/versions/`). To generate
a new migration after changing models: `alembic revision --autogenerate -m "..."`,
then review the generated file before applying — autogenerate doesn't catch
everything (e.g. some column renames show up as drop+add).
