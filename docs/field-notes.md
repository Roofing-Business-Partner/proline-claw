# ProLine API — Field Notes & Gotchas

Discovered during live API testing. These apply to all tenants unless noted.

---

## Contact Name Splitting

**Problem:** `edit/project` has a `contact_name` field that ProLine attempts to split into first/last. It splits on the LAST space only.

**Example:**
- Sent: `contact_name: "Jamie Sand Rivera"`
- Result: first = "Jamie Sand", last = "Rivera" ❌

**Fix:** Always use `contact_fname` + separate `contact_lname` (or careful full name). Do NOT use `contact_name` for new contacts.

**Edge cases to watch:**
- Hyphenated last names: "Jean-Claude Van-Damme" → could split incorrectly
- Multi-word last names: "Doug Van Martin" → will split as first="Doug Van", last="Martin"
- Single name / no last name → test before relying on it
- Names with suffixes: "John Smith Jr." → suffix may land in wrong field

**Rule:** Always pass first and last name as separate fields. Validate before writing.

---

## edit/contact Lookup Behavior

**Problem:** `edit/contact` returns `"Contact does not exist and first name is empty"` even when passing a valid `contact_id`, `contact_email`, or `contact_phone`.

**Status:** Unknown — possibly a permissions issue, possibly requires contacts to be created via a specific flow, or the endpoint requires a combination of fields we haven't identified yet.

**Workaround:** Use `edit/project` with a known `project_id` to update contact fields on an existing project/contact pair.

---

## edit/project — contact_lname Rejected

**Problem:** `edit/project` returns `"Invalid key found: \"contact_lname\""` — the field exists in the docs but is rejected by the API.

**Workaround:** Use `contact_fname` + `contact_name` (full name string) when updating via edit/project. Be aware of name splitting above.

---

## Stage Names vs Stage IDs

**Discovery:** `edit/project` accepts stage names as plain strings (not just IDs). ProLine fuzzy-matches to the closest stage.

**Example:**
- Sent: `"project_stage": "Appointment Set"`
- Matched to: `APPT SCHEDULED` (tenant's actual `stage_id`)

**Risk:** Fuzzy matching could map to the wrong stage if stage names are ambiguous. Use IDs when precision matters.

---

## events/edit — event_type Not Required

**Discovery:** `events/edit` works without an `event_type`. ProLine defaults to "Inspection" type.

**Duration:** Defaults to 60 minutes when not specified.

**Time zone:** Pass `"time_zone": "EST"` — ProLine maps to `America/New_York` correctly.

---

## Project Auto-Assignment

**Discovery:** New projects created via `edit/project` are automatically assigned to the ProLine account owner. No need to pass `project_assign` unless assigning to a different rep.

---

## Financial Fields — READ ONLY

The project response includes full financial data — useful for reporting:
- `quoted_value` — estimate sent
- `approved_value` — signed contract value
- `accounts_receivable` — outstanding balance
- `gross_revenue`, `net_revenue`
- `gross_profit`, `gross_margin`
- `merchant_fees`, `refunds`, `chargebacks`

**⚠️ These fields are READ ONLY via the API.** Attempting to set `quoted_value`, `revenue`, `cost`, `gross_revenue` via `edit/project` returns `"Invalid key found"`. Financial data must be entered through the ProLine UI (via quoting/invoicing tools). We can read and report on them, but not write them.

---

## Stage Name Matching — Unreliable

**Discovery:** Stage names passed as strings to `edit/project` are NOT reliably matched.
- `"Appointment Set"` → matched to `APPT SCHEDULED` ✅ (first time only?)
- `"Proposal Sent"` → returned success but DID NOT change the stage ❌
- `"Quoted"` → returned success but DID NOT change the stage ❌

**The API silently accepts unmatched stage names and returns success without changing anything.**

**Rule:** Always use stage IDs for reliable stage transitions. String names are unreliable and dangerous — you'll get a false positive.

---

## Activity Endpoints — Currently Non-Functional

**Problem:** All three activity endpoints (`create_alert`, `create_call`, `create_message`) return `"Missing parameter"` errors even when the exact documented parameters are sent in the JSON body.

Tested with:
- Inline JSON, variable-interpolated JSON, form-encoded data
- HTTP/1.1 and HTTP/2
- Exact payloads from the official docs
- Minimal payloads and full payloads

All return the same error pattern:
```json
{"statusCode":400,"body":{"status":"MISSING_DATA","message":"Missing parameter for workflow alert: parameter alert_text"}}
```

**Possible causes:**
1. These endpoints require a ProLine "workflow" to be configured in the account first
2. Permission issue disguised as a data error
3. API bug — backend not reading the JSON body for these routes

**Status:** Non-functional as of 2026-03-09. Needs ProLine support investigation.

---

## Rate Limits — edit/project

Discovered `edit/project` has a rate limit of approximately **1 call per 5 seconds**.
Exceeding it returns:
```json
{"error":"Rate limit exceeded for /v1/edit/project. Try again in 4.33 seconds."}
```

Activity endpoints also have similar rate limits (~5 seconds).

**Rule:** Space API calls at least 6 seconds apart for same endpoint. Do not fire rapid sequential calls.
