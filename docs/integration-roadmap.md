# proline-claw — Integration Roadmap

---

## Current State (2026-03-09)

### ProLine CRM ✅ Partial
- **Connected:** Partner API authenticated, 7 endpoints working
- **Local DB:** SQLite with full schema (projects, contacts, events, quotes, invoices, deal quality, response tracking, notes history)
- **Daily sync script:** Built and tested
- **Blocked:** Activity read endpoints don't exist. Import endpoints permission-denied. Availability endpoint permission-denied.
- **Next:** Webhook ingestion via Make.com

### CallRail 🔜 Not Yet Connected
- **Current use:** Marketing attribution only — tracking which ads/campaigns generate inbound calls
- **NOT used for:** VoIP/calling service (that's ProLine)
- **Value:** Cost-per-lead by source, marketing ROI, call recordings
- **Needs:** API credentials from your CallRail account

### Make.com 🔜 Not Yet Connected
- **Purpose:** Middleware between ProLine webhooks and the agent
- **Needs:** A Make.com account (free tier works for low volume)

---

## Integration Priority Order

### Phase 1: ProLine Webhooks via Make.com (HIGH)
**Why:** Solves the project registry problem + gets us financial data
**Effort:** Medium — needs Make.com account + ProLine webhook config
**Delivers:**
- Automatic project discovery (no more blind spots)
- Quote amounts pushed to us in real time
- Invoice/payment tracking
- Stage change notifications

### Phase 2: CallRail API (HIGH)
**Why:** Delivers true operating costs (cost-per-lead, marketing ROI) — the most common owner-level question
**Effort:** Low-Medium — API key + docs review + sync script
**Delivers:**
- Cost per lead by marketing channel
- Lead source attribution matched to ProLine contacts
- Marketing ROI reporting
- Call recordings linked to projects

### Phase 3: ProLine Response Time Tracking (MEDIUM)
**Why:** Addresses the "left on read" problem — customers replying while reps are heads-down in the field
**Effort:** Medium — requires ProLine Workflow configuration
**Delivers:**
- Inbound customer activity detection
- Rep response time tracking
- Automated alerts when customers are waiting
- Response time metrics in daily briefing

### Phase 4: Request Additional ProLine API Access (MEDIUM)
**Why:** Unlocks bulk operations and scheduling intelligence
**Effort:** Low (just asking) — depends on ProLine's willingness
**Request list:**
- `events/availability` — check rep calendar before booking
- `import/contact` — bulk lead intake from external sources
- `import/tags` — programmatic tag management
- `files/create_project_file` — CompanyCam integration
- Fix `activity/create_alert/call/message` — activity logging
- Fix `edit/contact` — direct contact updates
- Add `list/projects` or fix `find/project` filters — pipeline listing

### Phase 5: CompanyCam Integration (LOW)
**Why:** Photos from inspections linked to projects
**Effort:** Needs CompanyCam API review
**Blocked by:** ProLine file upload permissions

### Phase 6: QuickBooks Integration (LOW — Future)
**Why:** Automated expense tracking + true P&L
**Effort:** Significant — QuickBooks API is complex
**Delivers:** Real operating costs, not just revenue

### Phase 7: Google Calendar Sync (LOW — Future)
**Why:** Appointment visibility without ProLine login
**Blocked by:** events/availability permission

---

## Tool Stack Status

| Tool | Role | API Status | Priority |
|------|------|-----------|----------|
| ProLine | CRM, Project Mgmt, VoIP, Scheduling | ✅ Partial | Active |
| CallRail | Marketing Attribution | 🔜 Needs credentials | High |
| Make.com | Webhook Middleware | 🔜 Needs access | High |
| CompanyCam | Field Photos | ❌ Not started | Low |
| QuickBooks | Accounting | ❌ Not started | Future |
| Google Calendar | Scheduling | ❌ Blocked | Future |
| Google Chat | Team Comms | ❌ Not started | Future |

---

## What the owner gets at each phase

| Phase | Owner's Experience |
|-------|--------------------|
| Phase 1 | "The agent knows about every deal in my pipeline — even ones I create manually" |
| Phase 2 | "The agent tells me what my marketing costs and which channels actually work" |
| Phase 3 | "The agent catches when my team leaves customers hanging and pings them" |
| Phase 4 | "The agent can book appointments and log activity without me touching the CRM" |
