# Shadchan Server — Client Integration Guide

This document describes the `shadchan-server` HTTP API in enough detail to
build a client against it (mobile app, web app, etc.) without reading the
server source. It covers every endpoint, every request/response shape,
authentication, and the two multi-step flows (photo upload, resume-based
candidate creation) that aren't obvious from a single endpoint in isolation.

## 1. What this server is

A backend for shadchanim (Jewish matchmakers) to manage a private roster of
male and female shidduch candidates: their personal details, family
(`relatives`), and character references (`references`). Each shadchan only
ever sees their own candidates — there is no cross-shadchan visibility or
matching logic in this server; it's a private CRM, not a matching engine.

Stack: FastAPI + SQLAlchemy + Postgres. Base path for all endpoints:
`/api/v1/shadchanim`. There is currently **no CORS middleware configured**
on the server — if the client is a browser-based web app served from a
different origin, the server will need `CORSMiddleware` added before
requests will succeed; this doesn't affect native/mobile clients.

## 2. Authentication

Every endpoint except none — all of them — require a Firebase Auth ID
token:

```
Authorization: Bearer <firebase-id-token>
```

- The client authenticates the end user with Firebase Auth (client SDK) and
  sends the resulting ID token on every request.
- The server verifies it against Firebase Admin SDK. A missing/malformed
  header or invalid/expired token → `401 Unauthorized`.
- A verified Firebase user maps to at most one `shadchan` row, matched by
  `firebase_uid`. Before calling any candidate endpoint, the user must have
  registered as a shadchan via `POST /api/v1/shadchanim` (see below) — that
  call is itself authenticated (it needs a valid token) but doesn't require
  an existing shadchan record.
- Every candidate/photo/extraction endpoint is scoped by `{shadchan_id}` in
  the path **and** additionally requires that the authenticated user's own
  shadchan record has that same id. Passing someone else's `shadchan_id` →
  `403 Forbidden`, even with a perfectly valid token. There is no
  "admin"/cross-shadchan access at all right now.

## 3. Data model

### Shadchan
```jsonc
{
  "id": 1,
  "name": "R. Cohen",
  "phone": "050-111-2222",
  "email": "cohen@shadchanim.example",
  "created_at": "2026-08-13T10:00:00",
  "updated_at": "2026-08-13T10:00:00"
}
```

### Relative
Attached to a candidate (male or female). One of `relation` enum values:
`אבא`, `אמא`, `אח או אחות`.
```jsonc
{
  "id": 5,
  "relation": "אבא",
  "name": "Yitzchak Cohen",
  "maiden_name": null,
  "occupation": "Accountant",
  "dob": "1970-03-01",
  "marital_status": "married",
  "details": null
}
```
On create, `relation` and `name` are required; everything else optional.

### Reference
`ref_type` enum: `רב/מלמד`, `חבר`, `משפחה`.
```jsonc
{
  "id": 9,
  "ref_type": "רב/מלמד",
  "name": "Rav Levi",
  "role_connection": "Rebbe at yeshiva",
  "phone": "050-999-8888",
  "details": null
}
```
On create, `ref_type` and `name` are required; everything else optional.

### MaleCandidate
```jsonc
{
  "id": 12,
  "shadchan_id": 1,
  "first_name": "Moti",
  "last_name": "Cohen",
  "dob": "2000-01-01",
  "height": 175,
  "address": "Bnei Brak",
  "picture_url": "https://s3.<region>.backblazeb2.com/...&X-Amz-Signature=...",
  "created_at": "2026-08-13T10:00:00",
  "updated_at": "2026-08-13T10:00:00",
  "talmud_torah": "...",
  "yeshiva_ketana": "...",
  "yeshiva_gedola": "...",
  "relatives": [ /* Relative[] */ ],
  "references": [ /* Reference[] */ ]
}
```

### FemaleCandidate
Same shape as `MaleCandidate` except the education fields are
`beit_yaakov`, `seminar`, `maslul` instead of `talmud_torah` /
`yeshiva_ketana` / `yeshiva_gedola`.

**Important about `picture_url`:** the field name is historical — it is
**not** a stable/permanent URL. See §6. It is only good for a limited time
(currently 1 hour) after the response that returned it and must be
re-fetched (by re-calling a read endpoint) if the client needs it later,
e.g. don't cache it long-term or store it as "the" image URL anywhere.

## 4. Endpoints

All paths below are relative to `/api/v1/shadchanim`. All request/response
bodies are JSON unless noted. All require `Authorization: Bearer <token>`.

### Register a shadchan
```
POST /api/v1/shadchanim
Body: { "name": str, "phone": str, "email": str }
201 -> ShadchanRead
409 -> already registered (this firebase user already has a shadchan row)
```
The `409` body is `{ "detail": { "message": "...", "shadchan": ShadchanRead } }`
(the only endpoint whose `detail` is an object rather than a string — see
§9) so the client can recover the existing `shadchan_id` without a second
call.

### Get my shadchan record
```
GET /api/v1/shadchanim/me
200 -> ShadchanRead
404 -> this firebase account hasn't registered as a shadchan yet
```
The canonical way to find the current user's `shadchan_id` after login —
call this once and use the returned `id` for every other endpoint below.
No need to persist it client-side across sessions.

### Update a shadchan
```
PATCH /api/v1/shadchanim/{shadchan_id}
Body: ShadchanUpdate ({ "name"?, "phone"?, "email"? }, every field optional)
200 -> ShadchanRead
403 -> shadchan_id isn't the authenticated user's own
```

### List candidates
```
GET /api/v1/shadchanim/{shadchan_id}/candidates
Query params (all optional):
  limit          int, default 50, 1..200
  offset         int, default 0
  age_min        int, 0..150
  age_max        int, 0..150
  height_min     int, >=0
  height_max     int, >=0
  address        string (substring match, case-insensitive)
  name           string (substring match against first_name OR last_name, case-insensitive)
200 -> ShadchanCandidatesRead
```
```jsonc
// ShadchanCandidatesRead
{
  "shadchan_id": 1,
  "male_candidates": [ /* MaleCandidate[] */ ],
  "female_candidates": [ /* FemaleCandidate[] */ ],
  "pagination": { "limit": 50, "offset": 0, "male_total": 3, "female_total": 5 }
}
```
Note: `limit`/`offset` apply independently to both the male and female
lists (each is paginated the same way); `male_total`/`female_total` are the
unfiltered-by-pagination counts (post-filter, pre-limit) for each side, for
building pagination UI. Filters apply to both lists identically — there is
no way to filter male and female candidates differently in one call.

### Get a single male / female candidate
```
GET /api/v1/shadchanim/{shadchan_id}/male-candidates/{candidate_id}
GET /api/v1/shadchanim/{shadchan_id}/female-candidates/{candidate_id}
200 -> MaleCandidateRead / FemaleCandidateRead
404 -> shadchan or candidate not found
```
Use this for a detail/edit page or a deep link instead of fetching the
whole list and filtering client-side.

### Create a male / female candidate
```
POST /api/v1/shadchanim/{shadchan_id}/male-candidates
POST /api/v1/shadchanim/{shadchan_id}/female-candidates
Body: MaleCandidateCreate / FemaleCandidateCreate
201 -> MaleCandidateRead / FemaleCandidateRead
400 -> picture_url was set but doesn't correspond to an uploaded object (see §6)
404 -> shadchan_id not found
```
```jsonc
// MaleCandidateCreate
{
  "first_name": "Moti",        // required
  "last_name": "Cohen",        // required
  "dob": "2000-01-01",         // required, ISO date
  "height": 175,                // optional
  "address": "Bnei Brak",       // optional
  "picture_url": null,          // optional, see §6 - must be a path returned by upload-url
  "talmud_torah": null,
  "yeshiva_ketana": null,
  "yeshiva_gedola": null,
  "relatives": [ { "relation": "אבא", "name": "Yitzchak" } ],   // optional, default []
  "references": [ { "ref_type": "רב/מלמד", "name": "Rav Levi" } ]  // optional, default []
}
```
`FemaleCandidateCreate` is identical except `talmud_torah` /
`yeshiva_ketana` / `yeshiva_gedola` are replaced by `beit_yaakov` /
`seminar` / `maslul`.

`relatives`/`references` on create are **whole-object replacement of the
candidate's family/reference list at creation time** — there's no separate
endpoint to add a relative/reference to an existing candidate later (see
Gaps, §8).

### Update a male / female candidate
```
PATCH /api/v1/shadchanim/{shadchan_id}/male-candidates/{candidate_id}
PATCH /api/v1/shadchanim/{shadchan_id}/female-candidates/{candidate_id}
Body: MaleCandidateUpdate / FemaleCandidateUpdate (every field optional)
200 -> MaleCandidateRead / FemaleCandidateRead
400 -> picture_url was set but doesn't correspond to an uploaded object
404 -> shadchan or candidate not found
```
Partial update semantics: only the fields present in the JSON body are
changed (standard PATCH). `MaleCandidateUpdate`/`FemaleCandidateUpdate` do
**not** accept `relatives`/`references` — those can only be set at create
time currently (see §8).

### Candidate photo upload
See the full flow in §6. Short version:
```
POST /api/v1/shadchanim/{shadchan_id}/upload-url
Body: { "content_type": "image/jpeg" | "image/png" | "image/webp" }
200 -> { "upload_url": str, "path": str, "expires_in": 300 }
```

### Candidate-from-resume extraction (draft, non-persisting)
See the full flow in §7. Short version:
```
POST /api/v1/shadchanim/{shadchan_id}/male-candidates/extract
POST /api/v1/shadchanim/{shadchan_id}/female-candidates/extract
Body: multipart/form-data, field "file" = the resume file (.pdf or .docx)
200 -> MaleCandidateDraft / FemaleCandidateDraft (same shape as Create, all fields optional/nullable, plus `notes`)
400 -> file is empty, unreadable/corrupted, password-protected, or no text could be extracted
415 -> unsupported file type (only .pdf and .docx are accepted - not legacy .doc)
502 -> the LLM call itself failed, client should let the user retry
```
This endpoint **does not save anything**. It's purely file-in, best-guess
structured-draft-out. The backend extracts the raw text from the file itself
(no client-side PDF/DOCX parsing needed) and sends that to the LLM. Any part
of the text that doesn't map onto a schema field comes back in `notes`
(verbatim Hebrew) rather than being dropped.

## 5. Enums (exact wire values)

```
RelationType:   "אבא" | "אמא" | "אח או אחות"
ReferenceType:  "רב/מלמד" | "חבר" | "משפחה"
```
These are the only valid values for `relatives[].relation` and
`references[].ref_type` on create; anything else → `422 Unprocessable
Entity`. Wire values are Hebrew on purpose (matching how this data is used
day-to-day) — the underlying stored representation is unaffected by this,
these are just the JSON strings the client sends/receives.

## 6. Photo upload flow (Backblaze B2, presigned URLs)

The image bytes **never pass through this backend** — the client uploads
directly to Backblaze B2 using a presigned URL, and the backend only ever
handles short-lived signed URLs + a validity check. Full sequence for
attaching a photo when creating a candidate:

1. **Request an upload slot**
   ```
   POST /api/v1/shadchanim/{shadchan_id}/upload-url
   Body: { "content_type": "image/jpeg" }
   ```
   Response:
   ```jsonc
   { "upload_url": "https://s3.<region>.backblazeb2.com/...(presigned)...", "path": "candidates/1/<uuid>.jpg", "expires_in": 300 }
   ```
   `content_type` must be exactly one of `image/jpeg`, `image/png`,
   `image/webp` — anything else is rejected with `422` before any B2 call
   happens. `expires_in` is seconds until `upload_url` stops working
   (currently 300s / 5 minutes) — request a fresh one if the user is slow to
   pick/upload a photo.

   **The server does not currently enforce a max file size** — validate
   client-side before uploading. Recommended cap: **5MB**; there's no
   reason a candidate photo should be larger, and nothing server-side will
   stop an oversized upload from succeeding today.

2. **Upload the image bytes directly to B2** — no Authorization header, no
   backend involvement:
   ```
   PUT <upload_url>
   Header: Content-Type: image/jpeg   (must exactly match what was requested in step 1)
   Body: <raw image bytes>
   ```
   A `Content-Type` mismatch between what was requested and what's sent on
   the PUT will cause B2 to reject the upload (the presigned URL's signature
   covers content-type).

3. **Create (or update) the candidate using `path` from step 1 as
   `picture_url`:**
   ```
   POST /api/v1/shadchanim/{shadchan_id}/male-candidates
   Body: { ..., "picture_url": "candidates/1/<uuid>.jpg" }
   ```
   The backend verifies that object actually exists in B2 before saving. If
   the PUT in step 2 never happened (or failed), this returns `400 Bad
   Request` — treat that as "re-upload and try again", not a generic create
   failure.

4. **Every time you read a candidate back** (create response, update
   response, or the candidates list), `picture_url` in the JSON is **not**
   the raw path from step 1 — it's a presigned, time-limited **GET** URL the
   backend generated on the fly for that response (currently valid ~1 hour).
   The client can `GET` it directly (no auth header needed, it's a signed
   URL) to display the image, but must not persist it as a permanent image
   URL — re-fetch the candidate to get a fresh one once it expires.

Updating an existing candidate's photo is the same 3-step flow, just
targeting `PATCH .../male-candidates/{id}` in step 3 with the new
`picture_url`. There's currently no "remove photo" affordance — sending
`picture_url: null` on PATCH is not distinguishable from "don't touch the
photo" (see §8).

## 7. Candidate-from-resume flow

The client uploads the resume **file itself** (`.pdf` or `.docx`) — this
backend extracts the text server-side, so the client does zero PDF/DOCX
parsing or structuring. The flow:

1. Client posts the raw resume file as multipart form data to get an
   LLM-normalized draft:
   ```
   POST /api/v1/shadchanim/{shadchan_id}/male-candidates/extract
   Content-Type: multipart/form-data
   Field "file": <the .pdf or .docx file, unmodified>
   ```
   Only `.pdf` and `.docx` are accepted (routed purely by filename
   extension, not the `Content-Type` header) — legacy `.doc` is **not**
   supported; reject it client-side with a clear message rather than
   uploading it and getting a `415`.

   Response is a `MaleCandidateDraft` / `FemaleCandidateDraft` — same field
   set as the Create schema plus `notes`, but **every field is
   optional/nullable** (including `first_name`/`last_name`/`dob`), because
   extraction is best-effort: any field not present or unclear in the resume
   comes back `null`, never fabricated. Anything in the resume that doesn't
   map onto a schema field is preserved verbatim (in Hebrew) in `notes`
   rather than being dropped.

2. **Nothing is persisted by step 1.** The client should show the draft to
   the shadchan for review/editing (fill in nulls, fix mis-mapped fields),
   then submit the corrected data through the normal
   `POST .../male-candidates` (or `female-candidates`) create endpoint —
   that call is what actually saves it. There is no separate "confirm"
   endpoint; confirmation *is* the ordinary create call.

3. Gender isn't inferred by the server — the client decides whether to hit
   the `male-candidates/extract` or `female-candidates/extract` endpoint
   based on which resume it is.

4. Error handling:
   - `415 Unsupported Media Type` — the file extension isn't `.pdf` or
     `.docx`. Not retryable; the client picked/generated the wrong file.
   - `400 Bad Request` — the file is empty, corrupted, password-protected,
     or no extractable text was found. Ask the user for a different file.
   - `502 Bad Gateway` — the LLM call itself failed (upstream/timeout) or
     its output didn't validate. Treat as transient and let the user retry
     with the same file.

   There is currently no server-side file size limit on this endpoint —
   validate a reasonable cap client-side (same recommendation as photo
   uploads, §6: nothing stops an oversized upload from being accepted and
   parsed today).

## 8. Known gaps / things NOT to design around

Worth knowing so the client doesn't assume capabilities the server doesn't
have yet:
- No endpoint to add/edit/remove a single `relative` or `reference` on an
  existing candidate — they're only set as a full list at candidate-create
  time. Changing a candidate's family info after creation currently isn't
  possible via the API.
- No delete-candidate endpoint.
- No "remove photo" — `picture_url` can be set/replaced but not explicitly
  cleared.
- No cross-shadchan search/matching endpoints — this is single-shadchan CRM
  only.
- No server-side max upload size enforcement for candidate photos (see §6).
- CORS is allow-listed per deployment via `CORS_ORIGINS` (server env var) —
  a new client origin needs that added server-side (and the B2 bucket's own
  CORS rule updated separately for direct photo uploads, see §6) before it
  can call the API from a browser.

## 9. Error shape

Standard FastAPI error body on any non-2xx:
```jsonc
{ "detail": "human-readable message" }
```
except `POST /api/v1/shadchanim`'s `409`, whose `detail` is an object (see
§4) rather than a string.

Status codes used across the API: `400` (bad request, e.g. missing
photo object, or an unreadable/corrupted resume file), `401` (missing/invalid
auth token), `403` (valid token, but not this shadchan's resource), `404`
(shadchan/candidate not found), `409` (duplicate shadchan registration),
`415` (unsupported resume file type on the extract endpoints), `422` (request
body failed schema validation — wrong enum value, missing required field,
out-of-range number), `502` (resume-extraction LLM call failed).

## 10. OpenAPI `servers`

The server supports a `PUBLIC_API_URL` env var that populates the OpenAPI
`servers` block, so a client generated from
`https://make-match-server.onrender.com/openapi.json` (openapi-generator,
etc.) defaults its base URL correctly instead of `http://localhost`. This
needs `PUBLIC_API_URL=https://make-match-server.onrender.com` set on the
deployment (Render dashboard → Environment) — check with whoever runs the
backend that it's set if a generated client shows the wrong base URL.
