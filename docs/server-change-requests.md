# Server change requests — Shadchan Server

Hand-off for whoever maintains `shadchan-server` (FastAPI + SQLAlchemy +
Postgres). Each item is a contract the UI will code against exactly as written.
Items are independent unless noted; S1–S4 unblock Phase B2 of
`docs/tasks/README.md`, S5 unblocks task 025, S6 is for a future deployment.

After any of these deploy, the UI runs `npm run api:pull && npm run api:types`
and commits the regenerated `api/docs.json` + `src/api/types.ts`.

---

## S1 — `GET /api/v1/shadchanim/me` must return 404, not 500, when unregistered

**Today:** a valid Firebase token whose `uid` has no `shadchan` row → `500
Internal Server Error` (plain text, ~2.3 s — an unhandled exception).

**Wanted:**
```
404  {"detail": "Shadchan not found"}
```
Likely a `.one()` → `.one_or_none()` + `HTTPException(404)` in the `/me` handler.

**UI consumer:** 021 removes the 5xx→onboarding workaround in `RequireAuth`.

---

## S2 — DELETE candidate

```
DELETE /api/v1/shadchanim/{shadchan_id}/male-candidates/{candidate_id}
DELETE /api/v1/shadchanim/{shadchan_id}/female-candidates/{candidate_id}

204  (no body)
403  token valid but shadchan_id is not the caller's
404  candidate not found under this shadchan
```
- Cascade-delete the candidate's `relatives` and `references` rows.
- Best-effort delete of the B2 object behind `picture_url`; do not fail the
  request if the object delete fails.

**UI consumer:** 022.

---

## S3 — PATCH semantics: `exclude_unset`, and accept relatives/references

### 3a. Absent vs null
Apply `body.model_dump(exclude_unset=True)` in both candidate PATCH handlers:
- a field **absent** from the body → untouched
- a field **explicitly `null`** → cleared (`picture_url`, `height`, `address`,
  every education column)

This is what lets the UI "remove photo" (`picture_url: null`) and clear a
height, which today is indistinguishable from "don't touch".

### 3b. Relatives / references on update
Add to both `MaleCandidateUpdate` and `FemaleCandidateUpdate`:
```python
relatives:  list[RelativeCreate]  | None = None
references: list[ReferenceCreate] | None = None
```
Semantics: **whole-list replacement** when present (delete existing rows, insert
the given ones — same as create). Absent → untouched. Response is the full
`*CandidateRead` as today.

**UI consumer:** 024.

---

## S4 — `sort` on the candidates list

```
GET /api/v1/shadchanim/{shadchan_id}/candidates?sort=<value>
```
| value | order |
| --- | --- |
| `created_desc` | `created_at DESC` — **default** |
| `created_asc` | `created_at ASC` |
| `age_asc` | `dob DESC` (youngest first) |
| `age_desc` | `dob ASC` |
| `name_asc` | `last_name, first_name ASC` |
| `name_desc` | `last_name, first_name DESC` |

Applied identically to both lists; pagination unchanged; invalid value → `422`.
Expose it as a Pydantic/`Literal` enum so it lands in the OpenAPI spec.

**UI consumer:** 023.

---

## S5 — favourites + notes

Columns on both `male_candidates` and `female_candidates`:
```python
is_favourite: bool        = False   # server default false
notes:        str | None  = None
```
- Add to `*CandidateRead`, `*CandidateCreate`, `*CandidateUpdate`.
- List filter: `GET .../candidates?favourites_only=true` → only rows with
  `is_favourite = true` (both lists).

Single-shadchan roster, so a column is enough — no join table.

**UI consumer:** 025.

---

## S6 — CORS (deployment only)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "<production origin>"],
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)
```
Not needed while the UI uses its proxies; it unblocks calling the server
directly via `VITE_API_BASE_URL`. Preflight currently returns `400`.

---

## Status board

| Item | Requested | Deployed | Spec re-pulled |
| --- | --- | --- | --- |
| S1 `/me` 404 | 2026-08-23 | already shipped 2026-08-15 (`6977549`) | |
| S2 DELETE | 2026-08-23 | 2026-08-24 | |
| S3 PATCH semantics + relations | 2026-08-23 | 2026-08-24 | |
| S4 sort | 2026-08-23 | 2026-08-24 | |
| S5 favourites + notes | 2026-08-23 | 2026-08-24 | |
| S6 CORS | 2026-08-23 | 2026-08-24 | |
