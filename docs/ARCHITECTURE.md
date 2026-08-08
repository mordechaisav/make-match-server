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

1. **Gender strategy — split only at the candidate table.** `male_candidates`
   and `female_candidates` remain separate tables (a male and female resume
   never share a row) — but every table that hangs *off* a candidate is now
   gender-unified: one `relatives` table, one `candidate_references` table.
   This superseded the original "strict separation everywhere" decision.
   The unified tables use a **dual nullable FK** — `male_candidate_id` and
   `female_candidate_id`, both nullable, with a `CHECK` constraint enforcing
   exactly one is set per row. This is the exact "Option A" that was floated
   and rejected at the very first schema decision, back when only
   `Candidates`/`Education` were gender-split — it turned out to be the
   right call once the split proved to be more churn than value for the
   satellite tables.
2. **Education — flattened onto the candidate row, no separate table.**
   `male_candidates` has `talmud_torah`, `yeshiva_ketana`, `yeshiva_gedola`
   (each a nullable institution-name string); `female_candidates` has
   `beit_yaakov`, `seminar`, `maslul`. One column per progression stage,
   holding the institution name for that stage — the stage itself is
   implied by which column is filled in, not by a `type` value. This
   replaced an earlier `male_education`/`female_education` 1:N design;
   the tradeoff is a candidate can now only record one institution per
   stage (no history of e.g. two different yeshiva ketanas).
3. **Parents + siblings merged into one `relatives` table — one row per
   person.** The old `parents` table stored father *and* mother together in
   a single row; `siblings` stored one row per sibling. Merging them meant
   reshaping parents to match: a `relatives` row is now one person, with a
   `relation` enum (`father` | `mother` | `sibling`) and a superset of
   columns, most of them relevant to only one relation:
   - `name` — always
   - `maiden_name` — mother only
   - `occupation` — father/mother only
   - `dob`, `marital_status`, `details` — sibling only
   A candidate's old single "parents" row is now up to 2 `relatives` rows
   (father, mother). `relatives` uses the dual-FK strategy from #1.
4. **References unified across gender.** `male_references`/
   `female_references` merged into one `candidate_references` table (also
   dual-FK). Named `candidate_references`, not `references` — `REFERENCES`
   is a reserved SQL keyword and picking a name that needs quoting
   everywhere wasn't worth it.
5. **Timestamps** — `created_at` / `updated_at` on every table, via a shared
   `TimestampMixin` (`app/models/mixins.py`).
6. **Pagination** — `GET /api/v1/shadchanim/{shadchan_id}/candidates` takes
   `limit` (default 50, max 200) and `offset` (default 0) query params,
   applied independently to the male and female lists, with per-list totals
   in the response so a client can page each side separately.

## 3. Entity-relationship diagram

```mermaid
erDiagram
    SHADCHANIM ||--o{ MALE_CANDIDATES : registers
    SHADCHANIM ||--o{ FEMALE_CANDIDATES : registers

    MALE_CANDIDATES ||--o{ RELATIVES : has
    FEMALE_CANDIDATES ||--o{ RELATIVES : has

    MALE_CANDIDATES ||--o{ CANDIDATE_REFERENCES : has
    FEMALE_CANDIDATES ||--o{ CANDIDATE_REFERENCES : has

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
        string picture_url "nullable"
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
        string picture_url "nullable"
        string beit_yaakov "institution name, nullable"
        string seminar "institution name, nullable"
        string maslul "institution name, nullable"
        datetime created_at
        datetime updated_at
    }
    RELATIVES {
        int id PK
        int male_candidate_id FK "nullable, dual-FK"
        int female_candidate_id FK "nullable, dual-FK"
        enum relation "father | mother | sibling"
        string name
        string maiden_name "mother only"
        string occupation "father/mother only"
        date dob "sibling only"
        string marital_status "sibling only"
        string details "sibling only"
        datetime created_at
        datetime updated_at
    }
    CANDIDATE_REFERENCES {
        int id PK
        int male_candidate_id FK "nullable, dual-FK"
        int female_candidate_id FK "nullable, dual-FK"
        enum ref_type "rabbi_teacher | friend | family"
        string name
        string role_connection
        string phone
        string details
        datetime created_at
        datetime updated_at
    }
```

Both `RELATIVES` and `CANDIDATE_REFERENCES` carry a `CHECK` constraint —
exactly one of `male_candidate_id` / `female_candidate_id` is non-null per
row. Neither has a plain unnamed `references` table name; SQL reserves that
word.

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
    enums.py                 # ReferenceType, RelationType
    shadchan.py
    candidate.py              # MaleCandidate, FemaleCandidate (incl. flattened education columns)
    relative.py                # Relative (dual-FK, one row per father/mother/sibling)
    reference.py               # CandidateReference (dual-FK)
  schemas/                # Pydantic request/response models
    candidate.py
    shadchan.py
  repositories/           # Query layer - owns eager-loading strategy
    candidate_repository.py
    shadchan_repository.py
  services/               # Business logic between routers and repositories
    candidate_service.py
    shadchan_service.py
  routers/
    shadchanim.py
scripts/
  create_tables.py        # dev-only: Base.metadata.create_all()
  seed_data.py             # dev-only: populate mock data for manual/API testing
tests/
  conftest.py              # in-memory SQLite per test, get_db override
  test_shadchanim.py
  test_candidates.py
  test_candidate_repository.py  # eager-loading query-count regression test
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
`MaleCandidateRead`/`FemaleCandidateRead` shape (`relatives`/`references`
both `[]` on a fresh candidate — nothing else has been added yet).

Body (male): `first_name`, `last_name`, `dob` required; `height`, `address`,
`picture_url`, `talmud_torah`, `yeshiva_ketana`, `yeshiva_gedola` optional.
Body (female): same required fields; optional `height`, `address`,
`picture_url`, `beit_yaakov`, `seminar`, `maslul`.

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
      "relatives": [
        { "relation": "father", "name": "...", "occupation": "..." },
        { "relation": "mother", "name": "...", "maiden_name": "..." },
        { "relation": "sibling", "name": "...", "marital_status": "..." }
      ],
      "references": [ { "ref_type": "rabbi_teacher", "name": "..." } ]
    }
  ],
  "female_candidates": [ "..." ],
  "pagination": { "limit": 50, "offset": 0, "male_total": 3, "female_total": 5 }
}
```

**Eager-loading strategy** (`app/repositories/candidate_repository.py`):
`selectinload` for both the `relatives` and `references` collections — both
are 1:N now (parents lost its 1:1 special case when it merged into
`relatives`), so there's no more `joinedload` in this codebase at all.
Stacking `joinedload` on two simultaneous one-to-many collections would
multiply the primary row by the product of each collection's size (a
Cartesian join) — correct once deduplicated with `.unique()`, but wastes
bandwidth on any candidate with more than a couple of relatives/references.
`selectinload` issues one extra `SELECT ... WHERE id IN (...)` per
collection instead — still exactly O(1) queries per collection (not O(n)
per candidate), so N+1 is avoided either way; this just avoids the
multiplication too — pinned by
`tests/test_candidate_repository.py` (asserts exactly 3 queries: candidates
+ relatives + references, regardless of row count). Education needs no
eager-loading strategy at all — it's plain columns on the candidate row,
included for free. Male and female results are two separate queries (two
separate tables), merged in the service layer.

## 6. Remaining follow-ups (not blocking, not decided here)

- [x] Auth/authorization on the shadchanim endpoints — see §8.
- [ ] `marital_status` value set, if the product wants it constrained later.

## 7. Local Postgres (docker-compose)

`docker-compose.yml` at the repo root runs Postgres 16, credentials matching
`.env.example` (`postgresql+psycopg2://postgres:postgres@localhost:5432/shadchan`),
data persisted in a named volume. Start it with `docker compose up -d`.

Migrations: `alembic upgrade head` (applies `alembic/versions/`). To generate
a new migration after changing models: `alembic revision --autogenerate -m "..."`,
then review the generated file before applying — autogenerate doesn't catch
everything (e.g. some column renames show up as drop+add).

## 8. Auth — Firebase ID tokens

The client app (outside this repo) handles Firebase sign-in and sends
`Authorization: Bearer <ID token>` on every request. This backend never
issues or stores passwords; it only verifies tokens with the Firebase Admin
SDK (`app/core/firebase.py`, credentials path from
`FIREBASE_CREDENTIALS_PATH`).

`app/core/auth.py` has three dependencies, layered:
- `verify_firebase_token` — verifies the token, 401 if missing/invalid/expired.
- `get_current_shadchan` — looks up the `Shadchan` row by the token's `uid`
  (via `firebase_uid`), `None` if this Firebase account never registered one.
- `require_own_shadchan` — 403 unless the resolved shadchan's `id` matches
  the `shadchan_id` path param. Used on every `/shadchanim/{shadchan_id}/...`
  route so a logged-in shadchan can only ever touch their own candidates.

**Registration** (`POST /api/v1/shadchanim`) requires a valid token too —
`firebase_uid` is taken from the verified token server-side, never from the
request body, so a client can't register a profile under someone else's
identity. A second registration attempt with the same `firebase_uid` is a
409. `firebase_uid` is nullable + unique on `shadchanim` (nullable so the
unique constraint doesn't block — Postgres treats NULLs as distinct — but
every row created through the API always has one set).
