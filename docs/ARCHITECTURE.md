# Problem 360 — Architecture (Phase 1)

## Folder structure
```
problem360/
├─ frontend/                 React + Vite + Tailwind
│  └─ src/
│     ├─ config/             constants (routes, statuses, localities), firebase.js (public web config)
│     ├─ services/           api.js (fetch + ID token)
│     ├─ context/            AuthContext (login/register/session; backend /me is source of truth)
│     ├─ routes/             AppRouter, guards (RequireAccount, RequireVerifiedOrg, PublicOnly)
│     ├─ components/ui/      Button, Field, Alert, Card, Badge, States, Logo
│     ├─ components/layout/  CitizenLayout (social shell), OrganizationLayout (workspace shell)
│     ├─ components/auth/    AuthShell, useForm
│     └─ pages/{public,citizen,organization,shared}
├─ backend/                  FastAPI (layers: api → services → repositories → Firestore)
│  └─ app/{api/routes, core, schemas, services, repositories}
├─ agent/                    Strands Decider + tools (Phase 4; kept separate from API routes)
├─ docs/
└─ firestore.rules           deny-all: clients never touch Firestore directly
```

## Route map
| Path | Who | Notes |
|---|---|---|
| `/` | public | choose citizen / organization |
| `/citizen/login`, `/citizen/register` | public | citizen auth |
| `/org/login`, `/org/register` | public | organization auth |
| `/app`, `/app/explore`, `/app/report/new`, `/app/my-reports`, `/app/groups`, `/app/notifications`, `/app/profile` | citizen | social-feed layout |
| `/org/dashboard`, `/org/settings` | organization (any status) | workspace layout |
| `/org/civic`, `/org/groups`, `/org/events`, `/org/updates`, `/org/members` | organization **Verified** | locked page otherwise |
| `/org/join?code=` | public | join an existing organization with an invite |
| `/admin/*` | admin | Phase 6 |

## Account model
One Firebase Auth infrastructure. `users/{uid}.accountType` ∈ `citizen | organization | admin`.
- Login pages are per type; logging into the wrong one signs out with a clear message.
- The backend reads `users/{uid}` on every protected request (claims are a convenience, not the authority).
- Registering as an organization creates the org as **pending** and the registrant as **owner**. Only an admin can set `verified`.
- `admin` is never self-registered.
- Multiple authorized members: `organization_members/{orgId}_{uid}` with `role` owner | admin | member (invitations in Phase 5).

## Firestore collections
Built in Phase 1: `users`, `organizations`, `organization_members`.

Planned: `posts`, `posts/{id}/comments`, `posts/{id}/likes`, `reports` (incidents), `decisions` (Strands output) with `decisions/{id}/audit`, `departments`, `volunteer_groups`, `group_members`, `events`, `event_registrations`, `org_updates`, `notifications`.

```
users/{uid}:  uid, email, displayName, accountType, locality, organizationId?, status, createdAt
organizations/{orgId}: name, category, description, locality, website?, verificationStatus, createdBy, createdAt
organization_members/{orgId_uid}: organizationId, uid, role, createdAt
```

## Run
```
cd backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # add service-account path
.venv/bin/uvicorn app.main:app --reload
.venv/bin/pytest

cd frontend && cp .env.example .env && npm install && npm run dev
```
Enable **Email/Password** in Firebase Authentication. Deploy `firestore.rules`.

## Phase 2 — API contract the UI expects (built in Phase 3)
`GET /api/posts?locality&category&q&mine` · `POST /api/posts` · `POST /api/posts/{id}/like` (toggle) · `GET|POST /api/posts/{id}/comments` · `GET /api/notifications`.
Post: `{id, author{uid,name,locality}, description, category, locality, locationText, createdAt, mediaUrl?, mediaType?, status, referenceId?, likeCount, commentCount, likedByMe, decision?{action,summary}}`.
`decision` is rendered only if the backend returns it. Preview without a backend: `VITE_DEMO_DATA=true` (labelled demo posts).

## Phase 3 — posts backend
Firestore: `posts` (+ `likes/{uid}`, `comments`), `notifications`, `decisions/{postId}` (+ `audit`), `incidents/{referenceId}`.
Reads use equality filters only (no composite indexes); text search and the duplicate time window are applied in code (Firestore has no full-text search; fine at city-pilot scale).
Permissions (backend): citizens create/like/comment/upload; organizations and admins can read; only the author or an admin sees a decision trace or retries a failed review.
Media: `POST /api/media` validates content by magic bytes and size, stores under `posts/{uid}/{random}.ext` in private Storage, feed returns 1-hour signed URLs.
The agent does not analyse images; media is stored and shown only.

## Phase 4 — Strands Decider
> Updated for the hackathon: the agent is now a planner → critic Strands graph with a red-flag hook that stops it on danger,
> code-computed facts and fail-closed text. See `../DESIGN.md` and `../agent/README.md`; the list below is the original Phase 4 layout.

- `agent/decider_client.py` — hosted Decider call with the kit's b09 contract (`noul` yes/no and `choice`). One call carries all four questions.
- `agent/tools.py` — five `@tool`s bound to one report; every call is recorded.
- `agent/engine.py` — real `strands.Agent` on Bedrock with `AgentChoice` structured output.
- `agent/enforce.py` — code owns safety: danger → FLAG_URGENT, duplicate → CHECK_DUPLICATE, vague → REQUEST_MORE_INFORMATION, unsafe community idea → ROUTE; each change is stored as an override.
- `backend/app/services/decision_service.py` — runs the engine, creates the structured incident (never by the model), stores decision/tool runs/audit, notifies the citizen, fails closed.
- Incidents have `humanApprovalRequired: true` and `departmentContacted: false`. A human review UI is Phase 6.


## Phase 5 — organization workspace
Collections: `volunteer_groups` (+ `members/{uid}`), `events` (+ `registrations/{uid}`), `org_updates`, `organization_invites`, `admin_audit`; `organization_members` now stores name/email.
API: `/api/org/*` (verified members; role matrix in `api/routes/org.py`), `/api/groups`, `/api/events`, `/api/updates` (citizens), `/api/admin/organizations` (admin only), `/api/trending`.
Rules enforced in the backend: verified organization required; org-scoped reads/writes (other orgs' events return 404); capacity, past and cancelled checks inside one Firestore transaction; events may link only to reports the Decider marked SUGGEST_COMMUNITY_ACTION.
Queries use single-field equality (no composite indexes); sorting is done in code.
Known limits: content created by an organization stays visible if it is later rejected (access is removed, content is not hidden); times are shown in the viewer's local time; no email delivery.
