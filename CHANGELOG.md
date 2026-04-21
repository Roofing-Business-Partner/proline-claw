# Changelog

All notable changes to `proline-claw` are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-04-21

### Added — initial public release

- **Skill definition** — `skills/SKILL.md` with 7 battle-tested workflow recipes (new lead intake, appointment booking, post-inspection notes + draft email, pipeline report, context-aware follow-up, response-time monitoring design, CallRail marketing attribution design)
- **API knowledge base** — `docs/api-overview.md`, `docs/endpoints.md`, `docs/permissions.md`, `docs/field-notes.md` covering all 18 tested ProLine Partner API endpoints (7 working, 4 broken, 7 permission-denied) with known quirks and workarounds
- **Partner key request guide** — `docs/partner-key-request.md` with an email template for requesting a ProLine partner key
- **Tenant ID discovery guide** — `docs/stage-ids.md` walking through how to discover your tenant's stage IDs, team member user IDs, and event type IDs
- **SQLite schema** — `schema/schema.sql` with 15 tables covering projects, contacts, events, quotes, invoices, deal quality, notes history, draft emails, response tracking, CallRail calls, weather checks, rain days, geocode cache, sync log, and webhook log
- **Response schema docs** — anonymized examples for `project`, `contact`, and `event` responses
- **Init script** — `scripts/init-db.py` creates a fresh SQLite database from the schema (idempotent)
- **Onboarding wizard** — `scripts/onboard.py` validates ProLine credentials, discovers your tenant's stage/rep IDs, seeds the local DB, and writes a `tenant-config.local.json`
- **Daily sync script** — `scripts/daily-sync.py` pulls projects from ProLine, scores deal quality, tracks notes history
- **Rain day engine** — `scripts/weather-check.py` with Open-Meteo + Nominatim (both free) for weather-aware job scheduling
- **Bash helpers** — `scripts/proline.sh` reusable functions for all 7 working endpoints
- **Pipeline scan** — `scripts/pipeline-scan.sh` quick CLI pipeline report
- **Example database** — `data/example.db` with a fictional "ExampleCo Roofing" pipeline showing what a well-instrumented tenant looks like (6 projects across A/B/C/F quality grades, 2 events, rain-day forecasts)
- **Webhook integration design** — `docs/webhooks.md` and `docs/integration-roadmap.md` documenting the ProLine → Make.com → agent flow
- **GitHub scaffolding** — issue templates (bug, feature), PR template, `CODEOWNERS`, contribution guide

### Origin

Converted from a one-off customer build. Original customer-specific data, credentials, and tenant IDs have been stripped. Authored by [RoofClaw](https://roofclaw.com). MIT-licensed.

[0.1.0]: https://github.com/Roofing-Business-Partner/proline-claw/releases/tag/v0.1.0
