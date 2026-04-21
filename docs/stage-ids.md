# Discovering your tenant's IDs

Every ProLine tenant has unique stage IDs, team member user IDs, and event type IDs. The API gives you no "list all stages" endpoint, so you have to discover them indirectly. This guide walks through each one.

**Shortcut:** `python3 scripts/onboard.py` does all of the below automatically and writes the results to `data/tenant-config.local.json`. The manual steps below are for when the wizard doesn't cover your case.

---

## Stage IDs

### Method 1 — from an existing project

If you already have a project ID (or can see one in ProLine), query it:

```bash
curl -s -X POST https://api.proline.app/v1/find/project \
  -H "PARTNER_KEY: $PROLINE_PARTNER_KEY" \
  -H "COMPANY_KEY: $PROLINE_COMPANY_KEY" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "<your-project-id>"}' | jq '.stage, .stage_id'
```

The response shows both the human-readable `stage` and the `stage_id` you need to use in API writes.

### Method 2 — by moving a test project

To discover a stage you haven't seen yet:

1. Create a test project via `edit/project` (no `project_id`) — it lands in your LEADS stage
2. In the ProLine UI, move that project into the stage you want the ID for
3. Re-query the project with `find/project` and read the `stage_id`
4. Record in `data/tenant-config.local.json`

### Status group vs. stage

ProLine distinguishes between **stage** (company-specific, configurable) and **status** (global, fixed). Common status values:

| Status | Typical stages |
|--------|----------------|
| Lead | New Lead, Leads |
| Inspection | Appt Scheduled, Inspection Set |
| Open | Quoted, Proposal Sent |
| Won | Contract Signed, Job Won |
| Complete | Job Complete, Install Done |
| Closed | Paid & Closed, Fully Paid |
| Lost | Lost Sale, Not Interested |
| Disqualified | Bad Lead, Duplicate |

Statuses are useful for filtering/aggregating; stages are required for writes.

---

## Team member user IDs

Look up a rep by their email:

```bash
curl -s -X POST https://api.proline.app/v1/find/team_member \
  -H "PARTNER_KEY: $PROLINE_PARTNER_KEY" \
  -H "COMPANY_KEY: $PROLINE_COMPANY_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_email": "rep@yourcompany.com"}' | jq '.user_id, .name, .email'
```

You can also look up by name or phone number. Record each rep's `user_id` in `data/tenant-config.local.json`:

```json
{
  "reps": [
    {"name": "Rep Name", "email": "rep@yourcompany.com", "user_id": "..."}
  ]
}
```

Rep user IDs are needed whenever you book an appointment (`events/edit` → `assignee`) or assign a project.

---

## Event type IDs

Event types are defaulted. If you don't pass `event_type` when calling `events/edit`, you get **Inspection, 60 min**. That's usually fine.

To discover additional event type IDs, query an existing event:

```bash
curl -s -X POST https://api.proline.app/v1/find/event \
  -H "PARTNER_KEY: $PROLINE_PARTNER_KEY" \
  -H "COMPANY_KEY: $PROLINE_COMPANY_KEY" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "<project-with-the-event-type-you-want>"}'
```

Find the event you care about in the response and read its `type` field.

---

## Recording what you find

Store discovered IDs in `data/tenant-config.local.json` (gitignored):

```json
{
  "company_name": "Your Company",
  "leads_stage_id": "...",
  "appt_scheduled_stage_id": "...",
  "won_stage_id": "...",
  "lost_stage_id": "...",
  "default_rep_user_id": "...",
  "reps": [
    {"name": "...", "email": "...", "user_id": "..."}
  ],
  "event_types": {
    "inspection": "default"
  }
}
```

The skill's recipes reference these by key — agents that use this skill should read this file at startup and substitute the values when composing API payloads.

---

## Why there's no "list stages" endpoint

ProLine doesn't currently expose a directory-style endpoint for stages, teams, or event types. This is a known gap — see `docs/integration-roadmap.md` for what we've asked them to add. Until then, discovery is indirect but reliable once done.
