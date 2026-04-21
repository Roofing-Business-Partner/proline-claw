# ProLine API — Full Endpoint Reference

---

## find/project
`POST https://api.proline.app/v1/find/project`
Returns one matching project. At least one filter required.

**Request fields:**
- `project_id` — ProLine project ID
- `project_external_id` — your system's ID
- `contact_id` — contact ID
- `project_address1`, `project_city`, `project_state`, `project_zip`
- `project_stage` — stage ID
- `project_status` — "Lead", "Inspection", "Open", "Won", "Complete", "Closed", "Lost", "Disqualified"

---

## edit/project
`POST https://api.proline.app/v1/edit/project`
Creates a new project (no project_id) or updates existing (with project_id).

**Key fields:**
- `project_id` — omit to create, include to update
- `project_name`, `project_stage` (string name or ID), `project_notes`
- `project_address1/2`, `project_city`, `project_state`, `project_zip`
- `project_category`, `project_type`, `project_services[]`, `project_tags[]`
- `project_custom_field_1–7`
- `contact_fname`, `contact_name` (full string), `contact_phone`, `contact_email`
- `contact_type`, `contact_lead_source`, `contact_tags[]`
- `event_start_date` (MM/DD/YYYY HH:MM am), `event_type`, `event_time_zone`

**Notes:** `contact_lname` is rejected (invalid key). Use `contact_fname` + `contact_name`.

---

## find/contact
`POST https://api.proline.app/v1/find/contact`
Returns one matching contact.

**Request fields:**
- `contact_id`, `contact_phone`, `contact_email`
- `contact_address1`, `contact_city`, `contact_state`, `contact_zip`

---

## edit/contact
`POST https://api.proline.app/v1/edit/contact`
Updates an existing contact. **Currently unreliable via partner API** — see field-notes.md.
Workaround: update contact via `edit/project` using `project_id`.

---

## find/event
`POST https://api.proline.app/v1/find/event`

**Request fields:**
- `event_id`, `project_id`, `start_date` (ISO8601)
- `event_type`, `assignee`, `external_id`

---

## events/edit
`POST https://api.proline.app/v1/events/edit`
Creates or updates an appointment.

**Request fields:**
- `event_id` — omit to create, include to update
- `project_id` — required for new events
- `start_date` — ISO8601 (e.g. `"2026-03-11T19:00:00.000Z"`)
- `event_type` — optional, defaults to Inspection
- `assignee` — user ID of rep
- `time_zone` — e.g. `"EST"` → maps to America/New_York
- `external_id`, `external_reschedule_link`
- `skip_external_create` — "Yes"/"No"

**Defaults:** Duration = 60 min. Event type = Inspection.

---

## events/cancel
`POST https://api.proline.app/v1/events/cancel`

**Request fields:**
- `event_id` — required

---

## activity/create_alert
`POST https://api.proline.app/v1/activity/create_alert`

**Request fields:**
- `contact_id`, `project_id`
- `alert_text` — plain text
- `alert_extended` — optional HTML version

---

## activity/create_call
`POST https://api.proline.app/v1/activity/create_call`

**Request fields:**
- `contact` — contact ID
- `user` — user ID
- `type` — "incoming_call" or "outgoing_call"
- `duration` — seconds (integer)
- `recording` — URL to audio file
- `voicemail` — URL to voicemail file
- `external_id`, `call_note`

---

## activity/create_message
`POST https://api.proline.app/v1/activity/create_message`

**Request fields:**
- `contact` — contact ID
- `user` — user ID
- `type` — "incoming_message" or "outgoing_message"
- `message_body`, `message_note`, `external_id`

---

## find/team_member
`POST https://api.proline.app/v1/find/team_member`

**Request fields:**
- `proline_number` — phone number
- `user_email`
- `display_name`

**Response includes:** `user_id`, `display_name`, `proline_number`
