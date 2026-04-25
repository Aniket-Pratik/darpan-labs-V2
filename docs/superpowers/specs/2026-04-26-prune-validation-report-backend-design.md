# Prune Orphan Validation-Report Backend — Design Spec

**Date:** 2026-04-26
**Status:** Approved
**Scope:** Remove the validation-report REST endpoints, Pydantic schemas, SQLAlchemy model, Alembic table, and Celery task that were orphaned after the SDE frontend stopped consuming them (commits `0f79481`, `8e286f6`, `e0c1dc6` on `main`).

## Problem

The SDE frontend no longer calls any validation-report API. The corresponding backend surface is still implemented:
- 3 REST endpoints in `study-design-engine/app/routers/simulation.py` (lines 640–808).
- 3 Pydantic schemas in the same file.
- A `ValidationReport` SQLAlchemy model duplicated in `study-design-engine/app/models/twin.py` (lines 75–91) and `ai-interviewer/backend/app/models/twin.py` (lines 297–328).
- A `validation_reports` table created by `ai-interviewer/backend/migrations/versions/002_add_twin_pipeline_tables.py`.
- A `run_validation_report` Celery task in `ai-interviewer/backend/app/tasks/twin_tasks.py` (lines 405–606, ~200 lines).

Per cross-monorepo grep: zero callers in any frontend, test, script, or scheduled job. Per user decision (Option A): no historical data needs preserving.

## Non-Goals

- Not migrating any historical `validation_reports` rows — table treated as disposable.
- Not touching `validation-dashboard/scripts/` (the static-dashboard analysis pipeline is separate and stays).
- Not removing `pipeline_jobs` or any other shared table — only `validation_reports` is in scope.
- Not adding deprecation headers, 410 Gone responses, or sunset windows — clean delete, no external callers documented.

## Architecture

Five removals plus two Alembic migrations across two services:

### 1. SDE backend code deletions

- `study-design-engine/app/routers/simulation.py`: drop the three endpoint handlers (`create_validation_report`, `get_validation_report`, `list_validation_reports`) and the three Pydantic schemas (`ValidationReportRequest`, `ValidationReportResponse`, `ValidationReportDetail`). Approximate range: lines 640–808.
- `study-design-engine/app/models/twin.py`: drop the `ValidationReport` class (lines 75–91).
- `study-design-engine/app/models/__init__.py`: remove `ValidationReport` from any `__all__` and from re-exports.

### 2. ai-interviewer backend code deletions

- `ai-interviewer/backend/app/models/twin.py`: drop the duplicate `ValidationReport` class (lines 297–328).
- `ai-interviewer/backend/app/models/__init__.py`: remove `ValidationReport` from `__all__` and re-exports.
- `ai-interviewer/backend/app/tasks/twin_tasks.py`: drop the `run_validation_report` Celery task (lines 405–606).

### 3. SDE Alembic migration

New file at `study-design-engine/migrations/versions/<rev>_drop_validation_reports.py`. Revision parent is the current SDE head (`e5f6a7b8c9d0`). Implementation:

- `upgrade()`: `op.execute("DROP TABLE IF EXISTS validation_reports CASCADE")`.
- `downgrade()`: recreate the table with the same column set, foreign keys, and indexes that `ai-interviewer/backend/migrations/versions/002_add_twin_pipeline_tables.py` originally produced. The recreate path exists so a downgrade run is non-destructive of schema, even though the data is gone.

`IF EXISTS` makes the upgrade idempotent — safe whether the table is present in this environment or not.

### 4. ai-interviewer Alembic migration

New file at `ai-interviewer/backend/migrations/versions/<rev>_drop_validation_reports.py`. Revision parent is the current ai-interviewer head (whichever migration is the most recent). Same body shape as the SDE migration.

Two migrations are needed because the two services have independent Alembic histories sharing one database. The table could have been created by either history depending on which service ran migrations against the DB. `IF EXISTS` covers all cases.

## Data Flow / Effects

```
Pre-cleanup:  client → SDE endpoint → DB row + Celery dispatch
Post-cleanup: client → 404 (no route registered)
```

No data flow remains. The Celery task registration is dropped from the worker's task registry; if ai-interviewer's Celery worker is ever deployed, it simply won't know about `twin.run_validation_report` anymore.

## Components Affected

| File | Change |
|------|--------|
| `study-design-engine/app/routers/simulation.py` | Delete lines 640–808 (~168 lines) |
| `study-design-engine/app/models/twin.py` | Delete lines 75–91 (~17 lines) |
| `study-design-engine/app/models/__init__.py` | Remove export |
| `study-design-engine/migrations/versions/<new>.py` | New — drop table |
| `ai-interviewer/backend/app/models/twin.py` | Delete lines 297–328 (~32 lines) |
| `ai-interviewer/backend/app/models/__init__.py` | Remove export |
| `ai-interviewer/backend/app/tasks/twin_tasks.py` | Delete lines 405–606 (~202 lines) |
| `ai-interviewer/backend/migrations/versions/<new>.py` | New — drop table |

Net: ~−420 lines of code, +2 small migration files (~30 lines each).

## Commit Shape

Five commits, each atomic:

1. `sde-api: remove validation-report endpoints and schemas` — `simulation.py` only.
2. `sde-api: remove ValidationReport model + drop table migration` — SDE model files + new SDE migration.
3. `ai-interviewer: remove ValidationReport model + drop table migration` — ai-interviewer model files + new ai-interviewer migration.
4. `ai-interviewer: remove run_validation_report Celery task` — `twin_tasks.py` only.
5. (optional) PR/branch handoff.

Splitting code-from-table-drop into the same commit per service keeps the model and the schema-drop migration coherent: a future bisect that lands on commit 2 has both the Python class gone and the table gone in lockstep.

## Error Handling

- All migrations use `IF EXISTS` on the upgrade so re-running a partially-completed pass is safe.
- App start (`python -c "from app.main import app"` from each backend root) is the smoke check — any unresolved import means a deletion missed a reference.
- Pre-existing test failures from earlier work (4 unrelated frontend tsc errors) remain unrelated and untouched.

## Testing

- **SDE backend imports clean:** `cd study-design-engine && python -c "from app.routers import simulation; from app.models import *"` — no error.
- **ai-interviewer backend imports clean:** `cd ai-interviewer/backend && python -c "from app.models import *; from app.tasks import twin_tasks"` — no error.
- **SDE Alembic round-trip:** `alembic upgrade head` then `alembic downgrade -1` then `alembic upgrade head` — succeeds in a fresh local DB and one with the table pre-existing.
- **ai-interviewer Alembic round-trip:** same.
- **Existing test suite (if any) passes** — `pytest` from each backend root, no failures introduced. Pre-existing failures (if any) noted but not addressed.
- **Endpoint negative test:** after deploy, `curl -i https://api.try.darpanlabs.ai/api/v1/studies/<id>/validation-report` should return 404 (not 405, not 500).

## Rollback

Revert the five commits in reverse order. The downgrade migrations recreate the schema, so a Celery worker (if anyone re-deploys one) would land on a working table again. Data does not return.

## Branch

Direct commits to `main`, matching the prior session's policy. No feature branch.
