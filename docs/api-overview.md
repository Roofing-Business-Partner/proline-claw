# ProLine Partner API — Overview

Base URL: `https://api.proline.app/v1/`
Docs: https://docs.proline.app/partner-api

---

## Authentication

Two headers required on every request:

```
PARTNER_KEY: <partner_token>
COMPANY_KEY: <company_token>
```

- **PARTNER_KEY** — issued to approved partners by ProLine
- **COMPANY_KEY** — per-company token, found in the company's ProLine account under Settings → Integrations

## Rate Limits

Each endpoint has its own rate limit. Exceeding it returns:
`"condition is not met"`

## Error Patterns

| Response | Meaning |
|----------|---------|
| `"Unknown path /v1/xyz"` | Endpoint does not exist |
| `"Permission Denied"` | Endpoint exists, partner key not authorized |
| `"Invalid key found: \"field\""` | Field name not valid for this endpoint |
| `status: success` + `error: true` in body | Soft error — call accepted but operation failed |

---

## Endpoint Index

| Endpoint | Method | Access |
|----------|--------|--------|
| `/v1/find/project` | POST | ✅ |
| `/v1/edit/project` | POST | ✅ |
| `/v1/import/project` | POST | ❌ Permission Denied |
| `/v1/find/contact` | POST | ✅ |
| `/v1/edit/contact` | POST | ✅ (quirky — see field-notes.md) |
| `/v1/import/contact` | POST | ❌ Permission Denied |
| `/v1/find/event` | POST | ✅ |
| `/v1/events/edit` | POST | ✅ |
| `/v1/events/cancel` | POST | ✅ |
| `/v1/events/availability` | POST | ❌ Permission Denied |
| `/v1/activity/create_alert` | POST | ✅ |
| `/v1/activity/create_call` | POST | ✅ |
| `/v1/activity/create_message` | POST | ✅ |
| `/v1/import/activity` | POST | ❌ Permission Denied |
| `/v1/import/file` | POST | ❌ Permission Denied |
| `/v1/files/create_project_file` | POST | ❌ Permission Denied |
| `/v1/import/tags` | POST | ❌ Permission Denied |
| `/v1/find/team_member` | POST | ✅ |
