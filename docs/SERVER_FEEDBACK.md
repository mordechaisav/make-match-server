# Shadchan Server — feedback from building the client

Notes from implementing `shadchan-ui` against `CLIENT_INTEGRATION.md` and testing
every flow live against the deployed server. Organized by how much pain each gap
caused while building the real client, not by theoretical importance.

## Critical — blocks a feature entirely

### 1. `GET /api/v1/shadchanim/me` (or similar "who am I")

The biggest gap. After Firebase login there is no way to find the `shadchan_id`
belonging to the current `firebase_uid`. The client has to work around this by
stashing the id in `localStorage` after registration, with a manual "type in
your shadchan ID" fallback for when that's lost (new device, cleared storage,
different browser). That fallback is a dead end for a real user — they'd have
no way to know their own numeric ID.

Needs: `GET /shadchanim/me` → `ShadchanRead` if the firebase_uid has a row,
`404` if not. This single endpoint removes an entire class of client-side
workaround.

### 2. Fix `POST /shadchanim` on repeat calls

Right now a second registration attempt from the same firebase_uid returns
`409` with no id in the body — so the client learns "you're already
registered" but not *what your id is*, which is the only thing it actually
needs at that point. Either make registration idempotent (return `200` + the
existing `ShadchanRead` instead of `409`), or at minimum include the existing
`id` in the 409 error body. Combined with #1 this closes the gap completely.

### 3. B2 bucket CORS is not configured for browser uploads

Confirmed live: the client correctly gets a presigned URL from
`POST /upload-url`, but the browser's CORS preflight (`OPTIONS`) to that
Backblaze URL comes back **403**. Every browser-based client will fail here —
this isn't a frontend bug, it's the B2 bucket's CORS rules not permitting
`PUT` + `Content-Type` from any web origin.

Needs a CORS rule on the bucket allowing at least `PUT` and the `Content-Type`
header from the frontend's origin(s) (dev + prod). Until this is fixed, photo
upload is unusable from any browser.

## Important — forces real inefficiency/workarounds

### 4. `GET /api/v1/shadchanim/{id}/male-candidates/{candidate_id}` (+ female)

There's no way to fetch a single candidate. The detail page, the edit page,
and the PDF-import review page all have to fetch the *entire* candidate list
and filter client-side just to show one record. This doesn't scale past a
small roster and means a deep link to a candidate's page can't refresh
cheaply. Basic REST completeness gap.

### 5. CORS on the main API itself

A live preflight `OPTIONS` against `/candidates` with an arbitrary origin
came back with no `Access-Control-Allow-Origin` (and a `400`, oddly, rather
than just omitting the header). Every browser client is currently forced
through a same-origin proxy because of this — `CLIENT_INTEGRATION.md` already
flags "no CORS," but living with it means no browser-hosted frontend can call
the API directly in production either. Needs explicit `CORSMiddleware` with
the known frontend origin(s) allow-listed.

### 6. Add `name` as a query param on `GET /candidates`

`age_min/max`, `height_min/max`, and `address` are all server-side filters,
but name search isn't — so the client can only search names within whatever
page it already fetched (default 50, max 200). Once a roster passes 200
candidates, name search silently misses people. Should be server-side like
the others.

### 7. `servers` block missing from the OpenAPI spec

No `servers` entry means every generated client (openapi-generator, etc.)
defaults its base URL to `http://localhost`, and every consumer has to patch
that themselves. Adding `servers=[{"url": "https://make-match-server.onrender.com"}]`
(or via FastAPI's `servers=` kwarg) makes generated clients work out of the
box.

## Worth doing — real gaps, lower urgency

### 8. Endpoints to add/edit/remove a single `relative` or `reference`

Already flagged in `CLIENT_INTEGRATION.md` §8, and hit directly while
building: the edit form has to disable the whole family/references section
with a "not supported" note, which is a genuinely bad experience for a
shadchan who just needs to fix one sibling's typo. Something like
`POST/PATCH/DELETE /male-candidates/{id}/relatives/{relative_id}` (and the
equivalent for references) would remove that limitation.

### 9. `DELETE` candidate endpoint

Also in §8. Hit this directly too — every test candidate created during
testing is now permanently stuck in that shadchan's roster with no way to
remove it via the API.

### 10. "Remove photo" affordance

Also §8 — `picture_url: null` on PATCH is indistinguishable from "leave it
alone," so there's no way to actually clear a photo once set.

### 11. `PATCH /shadchanim/{id}`

A shadchan can register once but never update their own name/phone/email
afterward.

### 12. Document (or enforce) a max upload size

The upload-url flow validates `content_type` but nothing in the docs says
what happens with a 50MB "photo." Worth either enforcing a size cap
server-side or documenting the expected limit so the client can validate
before uploading.
