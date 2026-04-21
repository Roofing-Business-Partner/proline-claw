# proline-claw — Quick Reference

One-page cheat sheet. Full docs live in `docs/` and `skills/SKILL.md`.

---

## What this is

An OpenClaw skill that connects an AI agent to ProLine CRM. Automates lead management, appointment booking, pipeline reporting, weather-based scheduling, and customer communications.

- **Harness:** [OpenClaw](https://github.com/openclaw) (or pre-built [RoofClaw](https://roofclaw.com))
- **License:** MIT

---

## API authentication

Every ProLine call requires **two** headers:

| Header | Source |
|---|---|
| `PARTNER_KEY` | Issued by ProLine — apply via [docs/partner-key-request.md](docs/partner-key-request.md) |
| `COMPANY_KEY` | ProLine → Settings → Integrations |

Stored in `.env` as `PROLINE_PARTNER_KEY` + `PROLINE_COMPANY_KEY`.

Base URL: `https://api.proline.app/v1/`

---

## What works (7 endpoints)

| Action | Endpoint | Method |
|--------|----------|--------|
| Find a project | `/v1/find/project` | POST `{"project_id":"..."}` |
| Create/update project | `/v1/edit/project` | POST (no `project_id` = create) |
| Find a contact | `/v1/find/contact` | POST `{"contact_id":"..."}` |
| Find events | `/v1/find/event` | POST `{"project_id":"..."}` |
| Book appointment | `/v1/events/edit` | POST (no `event_id` = create) |
| Cancel appointment | `/v1/events/cancel` | POST `{"event_id":"..."}` |
| Find team member | `/v1/find/team_member` | POST `{"user_email":"..."}` |

## What's broken (4 endpoints)
- `edit/contact` — "Contact does not exist" for all lookups
- `activity/create_alert` — "Missing parameter" regardless of payload
- `activity/create_call` — same
- `activity/create_message` — same

## What's blocked (7 endpoints)
- `import/project`, `import/contact`, `import/activity`, `import/file`, `import/tags`
- `files/create_project_file`
- `events/availability`

---

## Critical gotchas

| Issue | Rule |
|-------|------|
| **Name splitting** | Always use `contact_fname` + `contact_lname`. Never rely on `contact_name` auto-split. |
| **Stage changes** | Always use stage IDs, not string names. Strings silently fail. |
| **Financial fields** | READ ONLY via API. `quoted_value`, `revenue`, `cost` cannot be written. |
| **find/project filters** | Only `project_id` and `contact_id` work. Status, stage, address, city filters return empty. |
| **Rate limits** | ~5 seconds between calls to same endpoint. |
| **Notes field** | Single text blob, not an array. Overwrites on every write. Read first, then append. |

---

## Finding your tenant's IDs

Every ProLine tenant has different stage IDs, user IDs, and event type IDs. Use the onboarding wizard to discover them automatically:

```bash
python3 scripts/onboard.py
```

It writes `data/tenant-config.local.json` with your tenant's:
- Rep user IDs (by email)
- Stage IDs (LEADS, APPT SCHEDULED, etc.)
- Default event types

For a manual walkthrough, see [docs/stage-ids.md](docs/stage-ids.md).

---

## Local database

**Location:** `data/proline.db` (SQLite, created by `init-db.py`)
**Demo:** `data/example.db` (what a well-run instance looks like)

15 tables:
`projects` · `contacts` · `events` · `quotes` · `invoices` · `deal_quality` · `notes_history` · `draft_emails` · `response_tracking` · `callrail_calls` · `weather_checks` · `rain_days` · `geocode_cache` · `sync_log` · `webhook_log`

### Key queries

```sql
-- Pipeline by status
SELECT status, COUNT(*), SUM(quoted_value) FROM projects GROUP BY status;

-- Deals needing attention
SELECT p.project_name, d.grade, d.score FROM projects p
JOIN deal_quality d ON p.project_id = d.project_id
WHERE d.grade IN ('C','F');

-- Weather risk for tomorrow
SELECT job_address, precip_prob_max, precip_total_mm, risk_level
FROM weather_checks WHERE check_date = date('now','+1 day');

-- Overdue follow-ups
SELECT project_name, followup_date FROM deal_quality
WHERE followup_date < date('now') AND grade != 'F';
```

---

## Scripts

| Script | Purpose | Suggested schedule |
|--------|---------|--------------------|
| `init-db.py` | Create fresh DB from `schema/schema.sql` | Once, at install |
| `onboard.py` | First-run wizard — validate keys, discover tenant IDs | Once, at install |
| `daily-sync.py` | Sync ProLine → SQLite, score deals | 5am daily |
| `weather-check.py evening` | Evening weather forecast + risk scoring | 9pm daily |
| `weather-check.py morning` | Morning forecast + trend + GO/CALL decision | 5am daily |
| `proline.sh` | Bash helper functions for API calls | On demand |

---

## 7 workflow recipes

1. **New Lead Intake** — `edit/project` creates project + contact
2. **Book Appointment** — `events/edit` + stage update
3. **Post-Inspection Notes + Draft Email** — structured notes + context-aware email in CRM
4. **Pipeline Report** — SQLite queries on deal quality + financials
5. **Context-Aware Follow-Up** — read notes before composing, prevent duplicate outreach
6. **Response Time Monitoring** — detect "left on read" customers (needs ProLine Workflow + Make.com)
7. **Marketing Attribution** — CallRail cost-per-lead + ROI (needs CallRail API)

Full recipes in [skills/SKILL.md](skills/SKILL.md).

---

## Rain day decision engine

| Component | Source | Status |
|-----------|--------|--------|
| Job addresses | ProLine / local DB | ✅ |
| Geocoding | Nominatim (free) | ✅ Tested |
| Weather forecast | Open-Meteo (free) | ✅ Tested |
| Risk scoring | Configurable rubric | ✅ Built |
| Trend analysis | Evening vs morning comparison | ✅ Built |
| Notification cascade | ProLine + TBD | 🔜 Designed |
| Calendar rescheduling | ProLine events/edit | 🔜 Designed |

**Default rubric:**
- Rain ≥ 50% probability + ≥ 5mm → CALL
- Wind ≥ 40 km/h sustained → CALL
- Rain ≥ 70% + ≥ 10mm → AUTO-CALL (full trust mode)

---

## Webhook integration (designed, not connected)

ProLine sends webhooks on:
- **Project Created/Updated** — captures projects you didn't create via API
- **Quote Sent/Approved** — gives you financial data you can't write via API
- **Invoice Sent/Approved** — payment and AR tracking

Recommended flow: ProLine → Make.com → your agent → SQLite. See [docs/webhooks.md](docs/webhooks.md).

---

## Integration roadmap

| Phase | Integration | Priority | Status |
|-------|------------|----------|--------|
| 1 | ProLine Webhooks via Make.com | HIGH | Designed |
| 2 | CallRail API | HIGH | Not started |
| 3 | Response Time Tracking | MEDIUM | Designed |
| 4 | Additional ProLine API access | MEDIUM | Request-list ready |
| 5 | CompanyCam | LOW | Not started |
| 6 | QuickBooks | LOW | Future |
| 7 | Google Calendar | LOW | Future |

---

## Files quick index

| File | What's in it |
|------|-------------|
| `docs/api-overview.md` | Auth, error patterns, endpoint status table |
| `docs/endpoints.md` | Every endpoint with request/response fields |
| `docs/permissions.md` | What's open, blocked, and broken + why |
| `docs/field-notes.md` | Every gotcha discovered during testing |
| `docs/stage-ids.md` | How to discover your tenant's stage / user / event IDs |
| `docs/partner-key-request.md` | How to request a partner key from ProLine |
| `docs/webhooks.md` | Webhook payloads + Make.com integration design |
| `docs/pipeline-report-design.md` | Pipeline reporting architecture |
| `docs/rain-day-engine.md` | Full rain day system design |
| `docs/integration-roadmap.md` | Phased plan for all integrations |
| `schema/schema.sql` | DDL for all 15 local SQLite tables |
| `schema/project-response.md` | Project JSON schema (anonymized example) |
| `schema/contact-response.md` | Contact JSON schema (anonymized example) |
| `schema/event-response.md` | Event JSON schema (anonymized example) |
| `skills/SKILL.md` | OpenClaw skill definition + all 7 recipes |
| `tests/test-log.md` | Endpoint audit results |
