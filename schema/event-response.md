# ProLine — Event Response Schema

Source: Anonymized example based on a live `find/event` query.

---

## Full Response

```json
{
  "event_id": "1770000000002x400000000000000000",
  "external_id": "",
  "type": "Inspection",
  "duration": 60,
  "start_date": "2026-03-11T19:00:00.000Z",
  "end_date": "2026-03-11T20:00:00.000Z",
  "time_zone": "America/New_York",
  "assignee_name": "Pat Smith",
  "assignee_email": "pat@examplecoroofing.com",
  "assignee_proline": "5559876543",
  "assignee_id": "1690000000000x200000000000000000",
  "project_name": "Jamie Rivera",
  "project_address1": "123 Example Street",
  "project_address2": "",
  "project_city": "Tampa",
  "project_state": "FL",
  "project_zip": "33601",
  "project_id": "1770000000001x100000000000000000",
  "contact_name": "Jamie Rivera",
  "contact_email": "jamie.rivera@example.com",
  "contact_phone": "5551234567",
  "contact_time_zone": "America/New_York",
  "contact_id": "1770000000000x100000000000000000"
}
```

## Field Reference

| Field | Type | Notes |
|-------|------|-------|
| event_id | string | ProLine unique ID |
| type | string | Event type label (e.g. "Inspection") |
| duration | number | Minutes — defaults to 60 |
| start_date | ISO8601 | UTC |
| end_date | ISO8601 | UTC — calculated from duration |
| time_zone | string | Full tz name (e.g. "America/New_York") |
| assignee_id | string | Rep's ProLine user ID |
| project_id | string | Linked project |
| contact_id | string | Linked contact |
| contact_time_zone | string | Contact's local time zone |

---

**Note:** IDs shown above are illustrative placeholders.
