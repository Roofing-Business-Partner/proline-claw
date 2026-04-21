# ProLine API — Permission Tiers

Last audited: 2026-03-09

---

## Context

The ProLine Partner API is gated. Partners are approved individually, and certain endpoint groups require a higher permission tier. ProLine has expressed concern about AI agents reducing the need for paid user seats — which appears to be why automation-heavy endpoints (bulk import, file management, availability) are restricted by default.

---

## What We Can Do (7 endpoints confirmed working)

| Endpoint | Capability | Status |
|----------|-----------|--------|
| `find/project` | Look up a project by ID, address, status, stage | ✅ Verified |
| `edit/project` | Create new project OR update existing one | ✅ Verified |
| `find/contact` | Look up a contact by ID, phone, email, address | ✅ Verified |
| `find/event` | Look up events by project, assignee, date | ✅ Verified |
| `events/edit` | Create or reschedule appointments | ✅ Verified |
| `events/cancel` | Cancel an appointment | ✅ Accepted (not fully tested) |
| `find/team_member` | Look up a rep by email, phone, or name | ✅ Verified |

## Accepted But Not Actually Working (4 endpoints)

| Endpoint | Issue |
|----------|-------|
| `edit/contact` | Returns "Contact does not exist" for all lookup methods |
| `activity/create_alert` | Returns "Missing parameter" even with correct JSON body |
| `activity/create_call` | Returns "Missing parameter" even with correct JSON body |
| `activity/create_message` | Returns "Missing parameter" even with correct JSON body |

---

## What's Blocked (7 endpoints)

| Endpoint | Why It Matters | Notes |
|----------|---------------|-------|
| `import/project` | Bulk lead creation | Blocked — could reduce manual CRM entry |
| `import/contact` | Bulk contact creation | Blocked |
| `events/availability` | Check rep calendar before booking | Blocked — key for smart scheduling |
| `import/activity` | Backfill call/email history | Blocked |
| `import/file` | Attach docs to contacts/projects | Blocked |
| `files/create_project_file` | Attach docs to projects | Blocked |
| `import/tags` | Create lead sources, categories, tags | Blocked |

---

## Implications

- **Scheduling:** We can book appointments (`events/edit`) but cannot check availability first (`events/availability` blocked). Workaround: confirm with rep before booking, or book with a buffer and note it.
- **Lead intake:** We must use `edit/project` (which creates project + contact together) instead of `import/contact`. Works fine, just less direct.
- **Tags/categories:** Can't create new ones via API. Must be configured in the ProLine UI first, then referenced by name or ID.
- **Files:** Cannot attach files programmatically. Must be done manually in ProLine.

---

## Recommendation

Request the following from ProLine partnerships:
1. `events/availability` — essential for intelligent scheduling
2. `import/contact` — needed for lead intake from external sources (CallRail, web forms, etc.)
3. `files/create_project_file` — needed for CompanyCam integration
4. **Fix `activity/create_alert`, `create_call`, `create_message`** — returning "missing parameter" even with correct payloads. May need workflow configuration or API-side fix.
5. **Fix `edit/contact`** — unable to look up any contact for editing
6. **Financial field write access** — `quoted_value`, `revenue`, `cost` etc. are read-only via API. Writing them requires the ProLine quoting UI.
