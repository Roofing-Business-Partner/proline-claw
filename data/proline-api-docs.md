# ProLine Partner API Docs (offline reference copy)

**Canonical source:** https://docs.proline.app/partner-api
**This copy:** fetched 2026-03-09 for offline reference.

This file is a snapshot of ProLine's publicly published API documentation, included in this repo so the skill has a searchable local reference. ProLine owns this content. Always defer to the live docs at the URL above — they may have changed since this copy was taken.

---

## Authentication
Headers required on every request:
- `PARTNER_KEY` — partner token (approved partners only)
- `COMPANY_KEY` — company token from the company's ProLine integrations page

## Rate Limits
Each endpoint has its own rate limit. Returns "condition is not met" error if exceeded.

---

## Endpoints

### Project

#### Find Project
`POST https://api.proline.app/v1/find/project`
At least one key-value pair required. Returns one project.
```json
{
  "project_id": "...",
  "project_external_id": "...",
  "contact_id": "...",
  "project_address1": "...",
  "project_address2": "...",
  "project_city": "...",
  "project_state": "...",
  "project_zip": "...",
  "project_stage": "...",
  "project_status": "Open"
}
```
project_status values: "Lead", "Inspection", "Open", "Disqualified", "Lost", "Won", "Complete", "Closed"

#### Create/Edit Project
`POST https://api.proline.app/v1/edit/project`
```json
{
  "project_id": "...", "external_id": "...", "edit_contact_latest": "No",
  "project_name": "...", "project_location": "...", "project_area": "...",
  "project_assign": "email", "project_inside_sales": "email",
  "project_production": "email", "project_accounting": "email",
  "project_stage": "...", "contact_campaign": "...",
  "project_address1": "...", "project_address2": "...",
  "project_city": "...", "project_state": "...", "project_zip": "...",
  "project_category": "...", "project_type": "...",
  "project_services": ["..."], "project_tags": ["..."],
  "project_custom_field_1..7": "...", "project_notes": "...",
  "contact_id": "...", "contact_fname": "...", "contact_name": "...",
  "contact_phone": "...", "contact_email": "...",
  "contact_type": "...", "contact_lead_source": "...", "contact_tags": ["..."],
  "event_external_id": "...", "event_start_date": "MM/DD/YYYY HH:MM am",
  "event_type": "...", "event_time_zone": "CST", "event_skip_external_create": "Yes"
}
```

#### Import Project
`POST https://api.proline.app/v1/import/project`
Full project+contact creation. Accepts string values (not IDs) for stage, category, type, services.
Key fields: contact_first_name, contact_last_name, contact_email, contact_phone, project_name, stage, address, assignee (email), revenue, cost, lead_date, won_date, completed_date, closed_date, lost_date, disqualified_date

---

### Contact

#### Find Contact
`POST https://api.proline.app/v1/find/contact`
Returns one contact. At least one field required.
```json
{
  "contact_id": "...",
  "contact_phone": "...",
  "contact_email": "...",
  "contact_address1": "...",
  "contact_address2": "...",
  "contact_city": "...",
  "contact_state": "...",
  "contact_zip": "..."
}
```

#### Create/Edit Contact
`POST https://api.proline.app/v1/edit/contact`
```json
{
  "contact_id": "...", "contact_fname": "...", "contact_lname": "...",
  "contact_organization": "...", "contact_phone": "...", "contact_email": "...",
  "contact_type": "...", "lead_source": "...", "contact_tags": ["..."],
  "contact_notes": "...", "contact_address1": "...", "contact_address2": "...",
  "contact_city": "...", "contact_state": "...", "contact_zip": "...",
  "contact_campaign_id": "...", "external_id": "...",
  "custom_field_1..3": "...", "custom_date_1..3": "MM/DD/YYYY HH:MM",
  "time_zone": "CST"
}
```

#### Import Contact
`POST https://api.proline.app/v1/import/contact`
```json
{
  "first_name": "...", "last_name": "...", "email": "...", "phone": "...",
  "organization": "...", "address1": "...", "address2": "...",
  "city": "...", "state": "...", "zip": "...",
  "assigned": "<proline_user_id>", "contact_type": "Customer",
  "lead_source": "Google", "contact_tags": "VIP",
  "notes": "...", "custom_field_1..3": "...", "external_id": "..."
}
```

---

### Events

#### Find Event
`POST https://api.proline.app/v1/find/event`
```json
{
  "event_id": "...", "project_id": "...", "start_date": "ISO8601",
  "event_type": "...", "assignee": "...", "external_id": "..."
}
```

#### Create/Edit Event
`POST https://api.proline.app/v1/events/edit`
```json
{
  "event_id": "...", "project_id": "...", "start_date": "ISO8601",
  "event_type": "...", "assignee": "...", "time_zone": "CST",
  "external_id": "...", "external_reschedule_link": "...",
  "skip_external_create": "Yes"
}
```

#### Cancel Event
`POST https://api.proline.app/v1/events/cancel`
```json
{ "event_id": "..." }
```

#### Event Availability
`POST https://api.proline.app/v1/events/availability`
```json
{
  "user_id": "...", "start_date": "ISO8601",
  "end_date": "ISO8601", "event_type": "..."
}
```

---

### Activity

#### Create Alert
`POST https://api.proline.app/v1/activity/create_alert`
```json
{
  "contact_id": "...", "project_id": "...",
  "alert_text": "...", "alert_extended": "<p>HTML...</p>"
}
```

#### Create Call
`POST https://api.proline.app/v1/activity/create_call`
```json
{
  "contact": "...", "user": "...",
  "type": "incoming_call|outgoing_call",
  "duration": 120, "recording": "url", "voicemail": "url",
  "external_id": "...", "call_note": "..."
}
```

#### Create Message
`POST https://api.proline.app/v1/activity/create_message`
```json
{
  "contact": "...", "user": "...",
  "type": "incoming_message|outgoing_message",
  "message_body": "...", "message_note": "...", "external_id": "..."
}
```

#### Import Activity
`POST https://api.proline.app/v1/import/activity`
activity_type values: incoming_message, outgoing_message, incoming_email, outgoing_email, incoming_call, outgoing_call, notification

---

### Import

#### Import File
`POST https://api.proline.app/v1/import/file`
```json
{
  "file_name": "...", "file_url": "<public_url>",
  "contact_id": "...", "project_id": "..."
}
```

#### Create Project File
`POST https://api.proline.app/v1/files/create_project_file`
```json
{ "project_id": "...", "file_url": "<public_url>", "file_name": "..." }
```

#### Import Tags
`POST https://api.proline.app/v1/import/tags`
```json
{
  "contact_types": ["Customer", "Supplier"],
  "contact_tags": ["VIP", "Blacklist"],
  "lead_sources": ["Google", "Referral"],
  "project_types": ["Retail", "Insurance"],
  "project_categories": ["Commercial", "Residential"],
  "project_tags": ["Blacklist", "No Referral"],
  "project_services": ["Roofing", "Gutters"],
  "project_areas": ["Downtown", "Greenfield Estate"]
}
```

---

### General

#### Find Team Member
`POST https://api.proline.app/v1/find/team_member`
```json
{
  "proline_number": "5551234567",
  "user_email": "user@email.com",
  "display_name": "John Smith"
}
```

---

## Webhooks
Stage change webhooks configurable in ProLine.
Docs: https://help.proline.app/en/articles/12707242-proline-webhooks
