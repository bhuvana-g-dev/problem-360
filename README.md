# Problem 360: from problems to progress

A Strands Agents SDK agent that reviews civic problem reports from Madurai residents (English, Tamil or Tanglish) and decides the
next action: flag danger, check for a duplicate, ask for missing details, recommend a department, suggest safe neighbour help, or
hand it to a person. Code owns every fact that must never be wrong; a Strands hook stops the agents when someone may be in danger.

Built for "Strands SDK: Workshop to Ship" (AWS Builder Center). Design: [DESIGN.md](DESIGN.md). Idea: [IDEA.md](IDEA.md).
Failures found and fixed: [FAILURES.md](FAILURES.md).

## Results
Not measured yet. After `ss measure`, the only numbers to quote are in `results/MEASURE.md` and `results/FACTS.md`.

## Run the agent
Needs Python 3.12, Amazon Bedrock access (default model `us.amazon.nova-2-lite-v1:0`, `us-east-1`), Amazon Translate, and a
Strands Decider team key from awsugmdu.in. Credentials come from `aws configure` / `aws sso login` and environment variables in
your own terminal; never put them in files.
```powershell
python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt
$env:DECIDER_API_KEY = "<your team key>"         # in your terminal only
python -m agent.check                             # Decider, an ordinary report, a danger report
python -m agent.app "Live wire hanging near the bus stop, sparking" --category Electricity
ss bedrock                                        # one live Bedrock + Amazon Translate call
ss cases show; ss cases approve --by "Your Name"  # only after you have read and corrected every label
ss measure
```

## Run the platform (optional)
`backend/` (FastAPI + Firebase Admin) and `frontend/` (React + Vite) wrap the same agent: a citizen posts a report, the backend runs
`agent.engine.StrandsDeciderEngine` as a background task, stores the decision, tool runs and audit trail in Firestore, and fails
closed (ESCALATE + human review) if the agent cannot run. No department is ever contacted.
```powershell
cd backend; ..\.venv\Scripts\pip install -r requirements.txt; copy .env.example .env   # fill it in; never commit it
..\.venv\Scripts\uvicorn app.main:app --reload
..\.venv\Scripts\pytest                                                                # test doubles for Firestore, LLM, Decider
cd ..\frontend; copy .env.example .env; npm install; npm run dev
```
Firebase (free Spark plan is enough): enable Email/Password auth, create Firestore, deploy `firestore.rules` (deny all client access).
Media storage is pluggable (`STORAGE_BACKEND` in `backend/.env`): `local` (default, free, files in `backend/uploads/` behind
expiring signed links), `s3` (any S3-compatible store: Backblaze B2, Cloudflare R2, MinIO, Amazon S3) or `firebase` (Blaze plan).

Tests: `backend` 33 (accounts, permissions, posts, media + storage, agent graph + hook + fail-closed, org workspace);
`frontend` 12 (`npm.cmd test`). They use test doubles for Firestore, the LLM and the Decider; the Strands graph, hook, tools,
enforcement, API and permissions are the real code.

## Platform features
- **Citizens** post reports (text, optional photo or video), like, comment, see trending issues nearby (last 7 days of real reports and likes),
  join volunteer groups and register for events (capacity-safe; past or cancelled events refuse registration).
- **Organizations** register as *Pending*; nothing in the workspace works until an admin verifies them (enforced by the backend).
  Roles: owner, admin, member. Members join through a single-use, 7-day invite bound to one email (`/org/join`; no email is sent,
  copy the link yourself). Verified organizations run volunteer groups, events (safety notes required; cancelling notifies registrants)
  and updates.
- **Civic activity:** reports the agent judged safe for neighbours (litter, parks only; never urgent, electrical, water or crime) appear
  to verified organizations, who can organise an event linked to that report. The agent's community suggestion also lists real upcoming
  events nearby, found by code, not by the model.
- **Admins** are never self-registered. Register the person normally, then promote them on a trusted machine:
  ```powershell
  cd backend; $env:PYTHONPATH="."; ..\.venv\Scripts\python.exe scripts\make_admin.py person@example.com
  ```
  Admin API: `GET /api/admin/organizations?status=pending`, `PATCH /api/admin/organizations/<ORG_ID>/verification` with
  `{"status": "verified", "note": "..."}`. Every change is written to `admin_audit`. Verify only after checking real documents.
  An admin screen is not built yet.

## Layout
```
agent/      Strands agent (see agent/README.md)       cases.jsonl   human-labelled gold set (ss cases / ss measure)
backend/    FastAPI api → services → repositories     results/      written only by ss measure / ss ship / ss video
frontend/   React + Vite + Tailwind                   docs/         platform architecture (phases 1-5)
```
