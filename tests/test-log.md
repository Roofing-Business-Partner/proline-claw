# proline-claw — Test Log

A record of what was tested against the live ProLine Partner API, with dates. Add new entries when you verify endpoints against your own tenant — this is how we grow the shared knowledge base.

---

## 2026-03 — Initial API Exploration

**Environment:** Live ProLine Partner account (newly created, fresh tenant)

---

### Authentication
- ✅ Confirmed: `PARTNER_KEY` + `COMPANY_KEY` headers required on every call
- ✅ Confirmed: Keys work after correct assignment (initially swapped them, got auth errors — partner is the integrator key, company is the tenant key)

### Endpoint Permission Audit
- Tested all 18 documented endpoints
- ✅ 10 accessible, ❌ 7 permission denied, 1 quirky (`edit/contact`)
- See `docs/permissions.md` for full breakdown

### Contact Creation
- ❌ `import/contact` — Permission Denied
- ✅ `edit/project` (no `project_id`) — creates project + contact together
- **Test record shape:**
  - Contact: example customer name
  - Phone / email / address populated
  - Response includes a generated `contact_id` and `project_id`
- ⚠️ **Bug found:** `contact_name` field splits on last space only. "Jamie Sand Rivera" → first="Jamie Sand", last="Rivera". Fix: always use `contact_fname` + `contact_lname` separately.

### Contact Update
- ❌ `edit/contact` — returns 200 but errors with "Contact does not exist and first name is empty" for all lookup methods (`contact_id`, email, phone)
- ✅ `edit/project` with `project_id` — can update contact fields via project

### Project Stage Update
- ✅ `edit/project` accepts stage names as strings (not just IDs) — but unreliably (see below)
- Example: `"project_stage": "Appointment Set"` → fuzzy-matched to the tenant's `APPT SCHEDULED` stage
- The tenant's actual `stage_id` was returned on the subsequent `find/project` call

### Appointment Booking
- ❌ `events/availability` — Permission Denied (cannot check calendar first)
- ✅ `events/edit` — created appointment successfully without `event_type`
- Defaults: type=Inspection, duration=60 min
- Time zone: `"EST"` maps to `America/New_York` correctly

### Team Member Lookup
- ✅ `find/team_member` by email — returns `user_id`, `name`, `email`, `proline_number`
- Also works by `user_phone` and `user_name`

---

### Post-Appointment Workflow Testing

- ❌ `quoted_value`, `revenue`, `cost`, `gross_revenue` — all rejected as invalid keys on `edit/project`. Financial fields are **read-only**.
- ✅ `project_notes` — updatable via `edit/project` (but overwrites on every write — read first, then append)
- ✅ Stage change via stage ID — reliable
- ⚠️ Stage change via string name — **unreliable**. Some strings match; others silently return success without changing the stage. Always use stage IDs.
- ❌ `activity/create_alert` — "Missing parameter: alert_text" even with correct JSON body
- ❌ `activity/create_call` — "Missing parameter: contact" even with correct JSON body
- ❌ `activity/create_message` — "Missing parameter: contact" even with correct JSON body
- All activity endpoints tested with inline JSON, variable interpolation, form-encoded, HTTP/1.1, and HTTP/2. All fail identically.

### Rate Limits Discovered
- `edit/project`: ~1 call per 5 seconds
- `activity/*`: ~1 call per 5 seconds
- Error response: `"Rate limit exceeded for /v1/edit/project. Try again in X seconds."`

---

## Open Issues

1. `edit/contact` lookup not working — root cause unknown
2. `contact_lname` rejected on `edit/project` — docs say valid, API rejects
3. `events/availability` blocked — need ProLine to enable
4. `import/*` endpoints all blocked — need ProLine partner tier upgrade
5. **All activity endpoints non-functional** — "missing parameter" error regardless of payload format
6. **Stage name string matching unreliable** — silently returns success without changing stage. Must use stage IDs.
7. **Financial fields read-only** — cannot set `quoted_value`, `revenue`, `cost` via API

If you hit (or resolve) any of these against your own tenant, please add an entry below and open a PR.
