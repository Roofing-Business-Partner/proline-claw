#!/bin/bash
# proline.sh — Reusable ProLine API helpers
# Part of proline-claw (https://github.com/roofclaw/proline-claw)
#
# Source this file in your shell to get proline_* helper functions:
#   source scripts/proline.sh
# Requires: PROLINE_PARTNER_KEY and PROLINE_COMPANY_KEY in your environment.

PARTNER_KEY="${PROLINE_PARTNER_KEY}"
COMPANY_KEY="${PROLINE_COMPANY_KEY}"
BASE_URL="https://api.proline.app/v1"

if [ -z "$PARTNER_KEY" ] || [ -z "$COMPANY_KEY" ]; then
  echo "Warning: PROLINE_PARTNER_KEY or PROLINE_COMPANY_KEY is not set. Load .env first." >&2
fi

proline_call() {
  local endpoint=$1
  local payload=$2
  curl -s -X POST "${BASE_URL}/${endpoint}" \
    -H "PARTNER_KEY: ${PARTNER_KEY}" \
    -H "COMPANY_KEY: ${COMPANY_KEY}" \
    -H "Content-Type: application/json" \
    -d "${payload}"
}

# Find a project
# Usage: proline_find_project '{"project_status":"Lead"}'
proline_find_project() { proline_call "find/project" "$1"; }

# Create or update a project
# Usage: proline_edit_project '{"project_name":"Test","contact_fname":"John","contact_name":"John Doe",...}'
proline_edit_project() { proline_call "edit/project" "$1"; }

# Find a contact
# Usage: proline_find_contact '{"contact_email":"email@example.com"}'
proline_find_contact() { proline_call "find/contact" "$1"; }

# Find a team member
# Usage: proline_find_team_member '{"user_email":"rep@company.com"}'
proline_find_team_member() { proline_call "find/team_member" "$1"; }

# Find an event
# Usage: proline_find_event '{"project_id":"..."}'
proline_find_event() { proline_call "find/event" "$1"; }

# Create or update an event
# Usage: proline_edit_event '{"project_id":"...","start_date":"ISO8601","time_zone":"EST"}'
proline_edit_event() { proline_call "events/edit" "$1"; }

# Cancel an event
# Usage: proline_cancel_event '{"event_id":"..."}'
proline_cancel_event() { proline_call "events/cancel" "$1"; }

# Log an alert on a project/contact
# Usage: proline_alert '{"contact_id":"...","project_id":"...","alert_text":"..."}'
proline_alert() { proline_call "activity/create_alert" "$1"; }

# Log a call
# Usage: proline_log_call '{"contact":"...","user":"...","type":"incoming_call","duration":120}'
proline_log_call() { proline_call "activity/create_call" "$1"; }

# Log a message
# Usage: proline_log_message '{"contact":"...","user":"...","type":"outgoing_message","message_body":"..."}'
proline_log_message() { proline_call "activity/create_message" "$1"; }
