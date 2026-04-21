# SKILL.md — proline-claw

> OpenClaw skill for ProLine CRM integration. MIT-licensed.

---

## Skill description

Connect an OpenClaw-compatible agent to a ProLine CRM account via the Partner API. Enables creating leads, booking appointments, moving pipeline stages, composing context-aware follow-up emails, and reporting on pipeline data — without manual CRM entry.

---

## Harness integration

This skill expects to run inside an agent harness that provides the OpenClaw four-file convention:

- `claude.md` — system prompt / master behavior file
- `tools.md` — tool registry
- `identity.md` — agent persona and role
- `memory.md` — persistent memory conventions

If your harness uses those files, this skill slots in alongside them. If you don't have them, the easiest path is [RoofClaw](https://roofclaw.com) — see [`ROOFCLAW.md`](../ROOFCLAW.md).

When this skill's recipes reference "the agent," they mean the Claude (or compatible) model running inside that harness. The skill itself is stateless — all persistent context lives in the harness's memory and in the local SQLite DB at `data/proline.db`.

---

## Capabilities (current)

- Create a new lead (project + contact) in ProLine
- Look up an existing project or contact
- Move a project to a new stage
- Book an appointment with a team member
- Cancel an appointment
- Write structured notes and staged draft emails to a project
- Look up a team member by email, name, or phone
- Score deal quality from project notes (A/B/C/F grading)
- Detect rain-day risk per job for the next 7 days

## Capabilities (pending ProLine permission)

- Check rep availability before booking
- Bulk import contacts from external sources
- Attach files to projects
- Create tags, lead sources, categories
- Write to financial fields (`quoted_value`, `revenue`, `cost`)
- Write call/alert/message activity records

---

## Required environment variables

```
PROLINE_PARTNER_KEY=<your_partner_key>
PROLINE_COMPANY_KEY=<your_company_key>
```

See `docs/partner-key-request.md` for how to get the partner key. Company key is in ProLine → Settings → Integrations.

---

## Required tenant-specific IDs

Every ProLine tenant has unique stage IDs, rep user IDs, and event type IDs. Run `python3 scripts/onboard.py` once to discover them — it writes `data/tenant-config.local.json`:

```json
{
  "leads_stage_id": "<your tenant's LEADS stage id>",
  "appt_scheduled_stage_id": "<your tenant's APPT SCHEDULED stage id>",
  "default_rep_user_id": "<primary rep's user id>",
  "reps": [
    {"name": "...", "email": "...", "user_id": "..."}
  ]
}
```

Recipes below reference these by name — e.g. `{leads_stage_id}`. Substitute with the values from your `tenant-config.local.json`, or let the agent read the file at runtime.

---

## Workflow recipes

### 1. New Lead Intake
**Trigger:** New lead comes in (web form, CallRail, referral, etc.)
**Endpoint:** `edit/project` (no `project_id` — passing no ID creates a new record)

```
1. Collect: first name, last name, phone, email, address
2. POST /v1/edit/project with:
   - contact_fname (first name ONLY — no spaces)
   - contact_lname (last name)
   - contact_phone, contact_email
   - project_name (usually contact's full name)
   - project_address1, project_city, project_state, project_zip
3. Project created in LEADS stage, assigned to default rep
4. Save returned project_id and contact_id to SQLite for future use
```

**⚠️ Do NOT use `contact_name` as a full-name string.** Always pass `contact_fname` + `contact_lname` separately. ProLine splits `contact_name` on the last space, which breaks multi-word names ("Van Damme", "Van Martin", etc.).

---

### 2. Book an Appointment
**Trigger:** Lead qualified, ready for inspection
**Endpoints:** `events/edit` + `edit/project`

```
1. Have: project_id, rep's user_id, desired date/time
2. Convert local time to UTC ISO8601 (e.g. 2pm EST = 2026-03-11T19:00:00.000Z)
3. POST /v1/events/edit with:
   - project_id
   - start_date (ISO8601 UTC)
   - assignee (rep's user_id)
   - time_zone (e.g. "EST" → maps to America/New_York)
   - event_type is optional (defaults to Inspection, 60 min)
4. POST /v1/edit/project with:
   - project_id
   - project_stage: {appt_scheduled_stage_id}
```

**⚠️ Always use stage IDs, not string names.** String stage names silently fail.
**⚠️ `events/availability` is permission-denied.** Confirm availability with the rep out-of-band before booking.

---

### 3. Post-Inspection: Update Notes & Stage Draft Email
**Trigger:** Sales rep completes the inspection and provides update
**Endpoint:** `edit/project`

```
1. Collect from rep: inspection findings, customer objections, preferred
   options, quoted price, next steps, follow-up date
2. POST /v1/edit/project with:
   - project_id
   - project_notes: structured note with all context (format below)
   - project_stage: next stage ID (if applicable)
3. If follow-up email needed:
   a. Read notes back via find/project to get full context
   b. Compose context-aware email (address objections, include relevant links)
   c. Append email as "DRAFT EMAIL — READY TO SEND" in project_notes
   d. Rep opens ProLine, copies email, sends manually
```

**Notes format:**
```
INSPECTION NOTES (MM/DD/YYYY):
Rep: [name]

[Customer situation and timeline]

OBJECTION: [what they pushed back on]
PREFERRED OPTION: [what they're leaning toward]
QUOTED PRICE: $[amount] ([option name])

NEXT STEP: [specific action with context]
FOLLOW-UP DUE: MM/DD/YYYY

---

DRAFT EMAIL — READY TO SEND (MM/DD/YYYY)
To: [contact email]
Subject: [context-aware subject line]

[Personalized email body that addresses objections, doesn't repeat
what's already been said, and includes relevant links/resources]

--- END DRAFT ---
```

**Why this works:**
- Email is composed with full CRM context — no generic templates
- Rep doesn't have to remember the conversation or write from scratch
- Notes and email draft live on the project record for audit trail
- If/when ProLine enables email sending via API, this becomes fully automated

**⚠️ Financial fields (`quoted_value`, `revenue`, `cost`) are READ ONLY via API.** Quote amounts must be entered through ProLine's quoting UI. Reference them in notes but don't attempt to write them to financial fields.

**⚠️ Notes overwrite.** `project_notes` is a single text blob. Always read existing notes first, append new content, then write back. Never write a new note without the prior context.

---

### 4. Pipeline Report
**Trigger:** Scheduled or on-demand
**Source:** Local SQLite (`data/proline.db`) populated by `daily-sync.py`

```
1. Query projects joined with deal_quality:
   SELECT p.project_name, p.stage, p.quoted_value, p.approved_value,
          d.grade, d.score, d.followup_date
   FROM projects p
   LEFT JOIN deal_quality d ON p.project_id = d.project_id
   WHERE p.status IN ('Lead','Inspection','Open','Won');
2. Aggregate by stage, status, rep, or grade
3. Deliver report to owner via agent's preferred channel
```

**Note:** Financial fields only populate once data is entered via ProLine's quoting/invoicing UI (or streamed in via webhooks — see `docs/webhooks.md`).

---

### 5. Context-Aware Follow-Up (Pre-Email Check)
**Trigger:** Follow-up due date reached
**Endpoints:** `find/project`

```
1. Read project via find/project
2. Check notes for:
   - What was already discussed/sent
   - What objections exist
   - What the next step was supposed to be
   - Whether a draft email was already staged
3. Compose follow-up that builds on prior context
4. Append new draft email to notes
5. DO NOT duplicate previous outreach — check notes first
```

**This prevents embarrassing emails** that ask the same thing twice or ignore what the customer already told the rep.

---

### 6. Response Time Monitoring ("Left on Read" Detection)
**Trigger:** ProLine Workflow webhook on inbound customer activity
**Data sources:** ProLine (via Workflow → Webhook → Make.com → agent), optionally CallRail

**Problem:** ProLine automation drives outbound outreach to customers, but when customers reply, reps often leave them waiting. Activity history is not readable via API, so we can't detect this from polling alone.

**Architecture:**
```
Customer replies (inbound message/call/text)
  → ProLine Workflow detects inbound activity
    → Workflow step: "Send Webhook" → Make.com
      → Make.com records timestamp + contact + project
        → If no outbound response within threshold (e.g. 60 min)
          → Make.com alerts the agent (Telegram, Slack, email, etc.)
            → Agent logs to SQLite + alerts the assigned rep
```

**What you need configured in ProLine:**
1. Workflow trigger: "When inbound message/call received"
2. Workflow step: "Send Webhook" with payload including `contact_id`, `project_id`, timestamp, message type
3. Destination: your Make.com webhook URL

**Status:** Requires ProLine Workflow configuration + Make.com middleware. Cannot be built with API alone. Local schema is already in place (`response_tracking` table).

---

### 7. Marketing Attribution & Cost Tracking (CallRail)
**Trigger:** Daily sync or CallRail webhook
**Data source:** CallRail API

**What CallRail provides:**
- Which marketing channel generated each inbound call (Google Ads, Facebook, SEO, referral, etc.)
- Call recordings and duration
- Caller phone number (matchable to ProLine contact)
- Lead source attribution

**What you build:**
- Cost per lead by marketing channel
- Marketing ROI per campaign
- Lead source breakdown in daily/weekly reporting
- Match CallRail calls to ProLine contacts by phone number

**Status:** Not yet integrated in this repo. Local schema in place (`callrail_calls` table). Needs CallRail API credentials + a sync script.

---

## Known quirks

See `docs/field-notes.md` for the full list. Critical ones:

- **Names:** Use `contact_fname` + `contact_lname` separately — never rely on `contact_name` auto-splitting
- **Stages:** Use stage IDs — string names silently fail
- **`edit/contact`:** Non-functional — update contacts via `edit/project` with `project_id`
- **Activity endpoints:** All non-functional (`create_alert`, `create_call`, `create_message`) — log activity in `project_notes` instead
- **Financial fields:** Read-only via API — use ProLine UI
- **Rate limits:** ~5 seconds between calls to the same endpoint
- **`events/edit`:** Defaults to Inspection type, 60 min duration when not specified
- **`find/project` filters:** Only `project_id` and `contact_id` work. Status/stage/address/city filters return empty arrays — do not rely on them.
