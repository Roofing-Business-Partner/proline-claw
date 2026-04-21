#!/bin/bash
# pipeline-scan.sh — Scan all known projects and generate a pipeline report
# Part of proline-claw (https://github.com/roofclaw/proline-claw)
#
# Legacy CLI alternative to daily-sync.py. Reads project IDs from the local
# SQLite DB and re-queries each one live. Use daily-sync.py for persistent
# state; use this for a quick ad-hoc readout.
#
# Usage:
#   source scripts/proline.sh    # loads env vars
#   bash scripts/pipeline-scan.sh

PARTNER_KEY="${PROLINE_PARTNER_KEY}"
COMPANY_KEY="${PROLINE_COMPANY_KEY}"
BASE_URL="https://api.proline.app/v1"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DB_PATH="${SCRIPT_DIR}/../data/proline.db"

if [ -z "$PARTNER_KEY" ] || [ -z "$COMPANY_KEY" ]; then
  echo "Error: PROLINE_PARTNER_KEY or PROLINE_COMPANY_KEY is not set." >&2
  exit 1
fi

if [ ! -f "$DB_PATH" ]; then
  echo "Error: Local DB not found at $DB_PATH." >&2
  echo "Run 'python3 scripts/init-db.py' and 'python3 scripts/onboard.py' first." >&2
  exit 1
fi

PROJECT_IDS=$(sqlite3 "$DB_PATH" "SELECT project_id FROM projects;")

if [ -z "$PROJECT_IDS" ]; then
  echo "No projects in local DB. Run 'python3 scripts/onboard.py' or 'python3 scripts/daily-sync.py' first."
  exit 0
fi

echo "PIPELINE SCAN — $(date '+%Y-%m-%d %H:%M')"
echo "================================================"
echo ""

for PID in $PROJECT_IDS; do
    # Rate limit: 6 second spacing
    sleep 6

    RESULT=$(curl -s -X POST "${BASE_URL}/find/project" \
        -H "PARTNER_KEY: ${PARTNER_KEY}" \
        -H "COMPANY_KEY: ${COMPANY_KEY}" \
        -H "Content-Type: application/json" \
        -d "{\"project_id\": \"$PID\"}")

    python3 -c "
import json, sys, re

data = json.loads('''$RESULT''')
if not data.get('body'):
    print(f'  [!] Project {\"$PID\"} not found')
    sys.exit()

p = data['body'][0]
name = p['project_name']
stage = p['stage']
status = p['status']
rep = p['assigned_to_name']
quoted = p['quoted_value']
approved = p['approved_value']
revenue = p['gross_revenue']
notes = p['notes']
contact = p['contact_fname'] + ' ' + p['contact_lname']
email = p['contact_email']
phone = p['contact_phone']

# Parse notes for deal quality
has_close_date = bool(re.search(r'(CLOSE_DATE|FOLLOW.UP.DUE|decision.within)', notes, re.I))
has_objection = bool(re.search(r'OBJECTION:', notes, re.I))
has_amount = bool(re.search(r'(QUOTED PRICE|DEAL_AMOUNT|\\\$[\d,]+)', notes, re.I))
has_next_step = bool(re.search(r'NEXT.STEP:', notes, re.I))
has_followup = bool(re.search(r'(FOLLOW.UP|FOLLOW_UP)', notes, re.I))

score = sum([has_close_date, has_objection, has_amount, has_next_step, has_followup])
if score >= 5: grade = 'A'
elif score >= 3: grade = 'B'
elif score >= 1: grade = 'C'
else: grade = 'F'

print(f'[{grade}] {name}')
print(f'  Status: {status} / {stage}')
print(f'  Contact: {contact} | {email} | {phone}')
print(f'  Rep: {rep}')
print(f'  Quoted: \${quoted:,.0f} | Approved: \${approved:,.0f} | Revenue: \${revenue:,.0f}')
print(f'  Deal Quality: {grade} ({score}/5)')

missing = []
if not has_close_date: missing.append('close date')
if not has_objection: missing.append('objection')
if not has_amount: missing.append('deal amount')
if not has_next_step: missing.append('next steps')
if not has_followup: missing.append('follow-up date')
if missing:
    print(f'  Missing: {\", \".join(missing)}')
print()
" 2>/dev/null
done

echo "================================================"
echo "Scan complete."
