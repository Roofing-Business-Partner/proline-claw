# proline-claw

> An [OpenClaw](https://github.com/openclaw) skill that turns your AI agent into a ProLine CRM operator.
> Built and battle-tested against a live ProLine Partner deployment.
> MIT-licensed. Authored by [RoofClaw](https://roofclaw.com).

---

## What this is

`proline-claw` is a Claude-ready skill + knowledge base for the [ProLine](https://proline.app) roofing CRM. It lets your agent create leads, book appointments, manage pipeline stages, compose context-aware follow-up emails, score deal quality, and make weather-aware scheduling decisions — all against the ProLine Partner API, with a local SQLite mirror for reporting.

Everything in this repo came from real API testing, not docs speculation. What works, what's broken, and what's permission-blocked is all documented in `docs/permissions.md`.

---

## Features

### Working today
- **Lead creation** — Create projects + contacts via API
- **Appointment booking** — Schedule inspections with reps
- **Stage management** — Move deals through the pipeline (by stage ID)
- **Project notes** — Read/write structured notes with deal context
- **Draft email composition** — Context-aware emails staged inside CRM notes
- **Team member lookup** — Find reps by email, phone, or name
- **Pipeline reporting** — Local SQLite mirror with A/B/C/F deal quality scoring
- **Daily sync** — Automated ProLine → SQLite sync script
- **Weather monitoring** — Rain day decision engine with geocoding + forecasting (free APIs)

### Designed, not yet connected
- **Webhook ingestion** — ProLine → Make.com → agent (project, quote, invoice payloads)
- **Response time tracking** — "Left on read" detection for customer replies
- **CallRail integration** — Marketing attribution + cost per lead
- **Calendar rescheduling** — Automated rain day schedule cascade

---

## Prerequisites

### 1. An OpenClaw-compatible agent harness

`proline-claw` is a **skill** — it expects to run inside an OpenClaw harness that provides:

- `claude.md` — system prompt / master behavior file
- `tools.md` — tool registry
- `identity.md` — agent persona and role
- `memory.md` — persistent memory conventions

If you haven't built out a harness, the fastest path is [RoofClaw](https://roofclaw.com) — the roofing-customized build of OpenClaw that ships with this skill pre-installed and pre-configured. See [ROOFCLAW.md](ROOFCLAW.md) for details.

You can also use this skill with any Claude Code / Claude API project — the four files above are convention, not hard requirement.

### 2. ProLine Partner API credentials

ProLine requires **two** keys on every API call:

- `PROLINE_PARTNER_KEY` — issued to approved integration partners by ProLine. You must apply and describe your agent's use case — ProLine is selective about who gets partner access. See [docs/partner-key-request.md](docs/partner-key-request.md) for what to send them.
- `PROLINE_COMPANY_KEY` — per-company token from **ProLine → Settings → Integrations** in the account you're integrating with.

### 3. System dependencies

- Python 3.8+
- SQLite 3 (ships with macOS/Linux)
- `curl`

No pip installs required for core functionality.

---

## Quick start

```bash
# 1. Clone
git clone https://github.com/roofclaw/proline-claw.git
cd proline-claw

# 2. Set your credentials
cp .env.example .env
#   then edit .env and paste in PROLINE_PARTNER_KEY + PROLINE_COMPANY_KEY

# 3. Initialize your local database
python3 scripts/init-db.py

# 4. Run the first-time onboarding wizard
python3 scripts/onboard.py
#   Validates your keys, pulls your stage IDs + team, seeds your local DB.

# 5. From here, run the daily sync on a schedule
python3 scripts/daily-sync.py                  # recommended: 5am daily
python3 scripts/weather-check.py evening        # recommended: 9pm
python3 scripts/weather-check.py morning        # recommended: 5am

# 6. Query your pipeline
sqlite3 data/proline.db "SELECT project_name, stage, status FROM projects;"
sqlite3 data/proline.db "SELECT * FROM deal_quality WHERE grade IN ('C','F');"
```

To see what a well-run ProLine instance looks like before you've synced your own, peek at the included demo: `sqlite3 data/example.db "SELECT * FROM projects;"` — see [data/example-data-notes.md](data/example-data-notes.md).

---

## Architecture

```
                    ┌─────────────┐
                    │   ProLine   │
                    │   CRM API   │
                    └──────┬──────┘
                           │ REST (7 endpoints accessible)
                           │
                    ┌──────▼──────┐
                    │  Your Agent │
                    │  (OpenClaw) │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──────┐  ┌─▼──────┐  ┌──▼─────────┐
       │   SQLite    │  │ Scripts │  │  Open-Meteo │
       │  Local DB   │  │  Sync   │  │  + Nominatim│
       └─────────────┘  └────────┘  └────────────┘
              │
     ┌────────┼──────────────┐
     │        │              │
  Projects  Events     Deal Quality
  Contacts  Quotes     Weather Checks
  Notes     Invoices   Rain Days
  History   Tracking   Geocode Cache
```

---

## Repo structure

```
proline-claw/
├── README.md                   # This file
├── LICENSE                     # MIT
├── QUICK-REFERENCE.md          # One-page cheat sheet
├── CONTRIBUTORS.md             # Authors
├── ROOFCLAW.md                 # Want it pre-built?
├── .env.example                # Credential template
├── requirements.txt            # Dependencies
│
├── docs/                       # API knowledge base
│   ├── api-overview.md         # Auth, errors, endpoint index
│   ├── endpoints.md            # Full endpoint reference
│   ├── permissions.md          # What's accessible vs. blocked
│   ├── field-notes.md          # Gotchas and quirks
│   ├── stage-ids.md            # How to discover your tenant's IDs
│   ├── partner-key-request.md  # How to request a ProLine partner key
│   ├── webhooks.md             # ProLine webhook payloads + Make.com design
│   ├── pipeline-report-design.md
│   ├── rain-day-engine.md      # Weather-based scheduling system
│   └── integration-roadmap.md  # Phased integration plan
│
├── schema/
│   ├── schema.sql              # CREATE TABLE for all 15 tables
│   ├── project-response.md     # Example project JSON schema
│   ├── contact-response.md     # Example contact JSON schema
│   └── event-response.md       # Example event JSON schema
│
├── skills/
│   └── SKILL.md                # Skill definition + 7 workflow recipes
│
├── scripts/
│   ├── proline.sh              # Bash API helpers
│   ├── init-db.py              # Create fresh SQLite from schema.sql
│   ├── onboard.py              # First-run wizard
│   ├── daily-sync.py           # ProLine → SQLite sync
│   ├── weather-check.py        # Rain day decision engine
│   └── pipeline-scan.sh        # CLI pipeline report (legacy)
│
├── data/
│   ├── example.db              # Demo pipeline — what good looks like
│   ├── example-data-notes.md   # How to interpret the demo
│   └── proline-api-docs.md     # ProLine's published API reference
│
└── tests/
    └── test-log.md             # API audit results
```

---

## API access summary

Tested against the live ProLine Partner API as of 2026-03.

### Accessible (7 verified working)
`find/project` · `edit/project` · `find/contact` · `find/event` · `events/edit` · `events/cancel` · `find/team_member`

### Accepted but not functional (4)
`edit/contact` · `activity/create_alert` · `activity/create_call` · `activity/create_message`

### Permission denied (7)
`import/project` · `import/contact` · `events/availability` · `import/activity` · `import/file` · `files/create_project_file` · `import/tags`

See [docs/permissions.md](docs/permissions.md) for the full breakdown and workarounds.

---

## Want this pre-installed and running, with a harness included?

This skill is the open-source foundation. If you'd rather not assemble the harness yourself, **[RoofClaw](https://roofclaw.com)** is RoofingBusinessPartner's fully configured OpenClaw build for roofing contractors — this skill, plus a working agent, plus ongoing updates. See [ROOFCLAW.md](ROOFCLAW.md).

---

## License

MIT — see [LICENSE](LICENSE). Use it, fork it, ship it. Attribution appreciated but not required.

Contributions welcome. See [CONTRIBUTORS.md](CONTRIBUTORS.md).
