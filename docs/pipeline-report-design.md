# Pipeline Report — Design & Constraints

## The Goal
A roofing company owner should be able to say "tell me about my pipeline" and get:
- How much we can make (deal amounts)
- When we can make it (anticipated close dates)
- Why we don't have it yet (current objections)
- What we're going to do about it (next steps)
- When we're going to do it (follow-up dates)
- Which deals are missing critical data

## The Problem
`find/project` **only returns results when queried by `project_id` or `contact_id`**.

Every other filter returns empty, even when matching data exists:
- ❌ `project_status: "Lead"` → empty
- ❌ `project_stage: "<stage_id>"` → empty
- ❌ `project_state: "FL"` → empty
- ❌ `project_city: "Tampa"` → empty
- ❌ `project_address1: "4520 Bay Street"` → empty

**There is no "list all projects" or "find by status" capability in the current API.**

This means we cannot scan the pipeline through the API alone.

## Workaround Options

### Option A: Local Project Registry (Recommended)
Maintain a local file (`data/project-registry.json`) with every project_id and contact_id we create or discover. On each pipeline scan:
1. Read the registry
2. Query each project by ID
3. Parse notes + financial fields for deal quality
4. Build the report

**Pros:** Works within current API constraints. No ProLine changes needed.
**Cons:** We only know about projects we created or were told about. Misses projects created manually in ProLine UI.

### Option B: Webhook Ingestion
If ProLine webhooks are configured (stage change triggers), we can:
1. Receive webhook on stage change
2. Capture project_id + new stage
3. Add to local registry automatically

**Pros:** Catches ALL stage changes, even manual ones.
**Cons:** Requires ProLine webhook configuration + a webhook endpoint on our side.

### Option C: Request List Endpoint from ProLine
Ask ProLine to add a `/v1/list/projects` or enable `find/project` to return multiple results when filtering by status/stage.

**Pros:** Clean solution.
**Cons:** Depends on ProLine roadmap.

### Recommended Approach: A + B
Start with Option A (local registry) for immediate value. Add Option B (webhooks) when we set up the webhook endpoint. Request Option C from ProLine for the long term.

---

## Deal Quality Scoring

For each project in the pipeline, check for these in the notes:

| Data Point | Field/Location | Why It Matters |
|-----------|---------------|----------------|
| Anticipated close date | Notes (parsed) | "When can we make it?" |
| Current objection | Notes (parsed) | "Why don't we have it?" |
| Deal amount | `quoted_value` or Notes | "How much can we make?" |
| Next steps | Notes (parsed) | "What are we doing about it?" |
| Follow-up date | Notes (parsed) | "When are we doing it?" |
| Assigned rep | `assigned_to_name` | "Who owns this?" |

### Quality Grades
- **A — Complete:** All 5 data points present. Deal is being actively managed.
- **B — Workable:** 3-4 data points. Needs minor attention.
- **C — Stale:** 1-2 data points. Deal is drifting. Flag for action.
- **F — Dead file:** No context in notes, no follow-up date. Needs immediate rep attention.

---

## Notes Format (Standardized for Parsing)

For deal quality scoring to work, notes should follow a parseable format:

```
[SECTION_TYPE] (DATE):
Rep: [name]

CLOSE_DATE: MM/DD/YYYY
OBJECTION: [text]
DEAL_AMOUNT: $[number]
NEXT_STEP: [text]
FOLLOW_UP: MM/DD/YYYY
```

The agent should write notes in this format. When reading notes from manual entry, it should attempt to extract these fields with fuzzy matching.

---

## Daily Briefing Format

```
PIPELINE REPORT — [DATE]

SUMMARY:
- [X] total active deals
- $[Y] total pipeline value
- [Z] deals need attention

BY STATUS:
[STATUS]: [count] deals | $[value]
  ✅ [project_name] — $[amount] | Close: [date] | Next: [action]
  ⚠️ [project_name] — $[amount] | MISSING: [what's missing]
  🔴 [project_name] — No notes, no follow-up | NEEDS ATTENTION

DEALS MISSING DATA:
- [project_name]: Missing close date, objection
- [project_name]: No follow-up scheduled
- [project_name]: No deal amount recorded

OVERDUE FOLLOW-UPS:
- [project_name]: Follow-up was [date], [X] days overdue
```

---

## Implementation Plan

### Phase 1: Local Registry (Now)
1. Create `data/project-registry.json`
2. Auto-add every project we create via edit/project
3. Build scan function: read registry → query each → parse → score → report

### Phase 2: Webhook Capture (When Available)
1. Set up webhook endpoint
2. Capture stage changes → update registry
3. Catches manual ProLine activity

### Phase 3: Full Pipeline API (When ProLine Enables)
1. Replace registry scan with single API call
2. Keep registry as backup/cache
