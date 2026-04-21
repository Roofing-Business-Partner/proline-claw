#!/usr/bin/env python3
"""
daily-sync.py — ProLine → SQLite daily sync
Part of proline-claw (https://github.com/roofclaw/proline-claw)

Runs as a cron job (recommended: 5am local time).
No LLM tokens required — pure API + database operations.

Usage:
    python3 daily-sync.py

Requires env vars:
    PROLINE_PARTNER_KEY
    PROLINE_COMPANY_KEY

If the local DB doesn't exist yet, run `python3 scripts/init-db.py` first.
"""

import json
import subprocess
import sqlite3
import hashlib
import re
import time
import os
from datetime import datetime

# --- Config ---
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "proline.db")
PARTNER_KEY = os.environ.get("PROLINE_PARTNER_KEY", "")
COMPANY_KEY = os.environ.get("PROLINE_COMPANY_KEY", "")
BASE_URL = "https://api.proline.app/v1"
RATE_LIMIT_SECONDS = 6


def api_call(endpoint, payload):
    """Make a ProLine API call and return parsed JSON."""
    result = subprocess.run([
        'curl', '-s', '-X', 'POST', f'{BASE_URL}/{endpoint}',
        '-H', f'PARTNER_KEY: {PARTNER_KEY}',
        '-H', f'COMPANY_KEY: {COMPANY_KEY}',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps(payload)
    ], capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": result.stdout}


def notes_hash(text):
    """Hash notes for change detection."""
    return hashlib.md5((text or "").encode()).hexdigest()


def parse_deal_quality(notes):
    """Parse notes for deal quality scoring."""
    if not notes:
        return {
            "has_close_date": 0, "has_objection": 0, "has_deal_amount": 0,
            "has_next_steps": 0, "has_followup_date": 0, "score": 0, "grade": "F",
            "close_date": None, "objection": None, "deal_amount": None,
            "next_steps": None, "followup_date": None
        }

    has_close = 1 if re.search(r'(CLOSE.DATE|FOLLOW.UP.DUE|decision.within)', notes, re.I) else 0
    has_obj = 1 if re.search(r'OBJECTION:', notes, re.I) else 0
    has_amt = 1 if re.search(r'(QUOTED PRICE|DEAL.AMOUNT|\$[\d,]+)', notes, re.I) else 0
    has_next = 1 if re.search(r'NEXT.STEP:', notes, re.I) else 0
    has_fu = 1 if re.search(r'(FOLLOW.UP|FOLLOW_UP)', notes, re.I) else 0

    score = has_close + has_obj + has_amt + has_next + has_fu
    grade = 'A' if score >= 5 else 'B' if score >= 3 else 'C' if score >= 1 else 'F'

    # Extract values
    close_match = re.search(r'(?:CLOSE.DATE|FOLLOW.UP.DUE):\s*(\S+)', notes, re.I)
    obj_match = re.search(r'OBJECTION:\s*(.+?)(?:\n|$)', notes, re.I)
    amt_match = re.search(r'(?:QUOTED PRICE|DEAL.AMOUNT):\s*\$?([\d,]+)', notes, re.I)
    next_match = re.search(r'NEXT.STEP:\s*(.+?)(?:\n|$)', notes, re.I)
    fu_match = re.search(r'FOLLOW.UP(?:.DUE)?:\s*(\S+)', notes, re.I)

    return {
        "has_close_date": has_close,
        "has_objection": has_obj,
        "has_deal_amount": has_amt,
        "has_next_steps": has_next,
        "has_followup_date": has_fu,
        "score": score,
        "grade": grade,
        "close_date": close_match.group(1) if close_match else None,
        "objection": obj_match.group(1).strip() if obj_match else None,
        "deal_amount": float(amt_match.group(1).replace(',', '')) if amt_match else None,
        "next_steps": next_match.group(1).strip() if next_match else None,
        "followup_date": fu_match.group(1) if fu_match else None
    }


def extract_draft_email(notes):
    """Extract draft email from notes if present."""
    match = re.search(
        r'DRAFT EMAIL.*?\n'
        r'To:\s*(.+?)\n'
        r'Subject:\s*(.+?)\n\n'
        r'(.+?)'
        r'---\s*END DRAFT\s*---',
        notes, re.S | re.I
    )
    if match:
        return {
            "to": match.group(1).strip(),
            "subject": match.group(2).strip(),
            "body": match.group(3).strip()
        }
    return None


def build_clean_notes(project, deal_quality):
    """Build clean current-state notes for ProLine."""
    lines = [f"LAST UPDATED: {datetime.now().strftime('%m/%d/%Y')}"]

    if project.get('assigned_to_name'):
        lines.append(f"REP: {project['assigned_to_name']}")

    lines.append(f"STATUS: {project.get('status', 'Unknown')} / {project.get('stage', 'Unknown')}")
    lines.append("")

    if deal_quality['close_date']:
        lines.append(f"CLOSE DATE: {deal_quality['close_date']}")
    if deal_quality['objection']:
        lines.append(f"OBJECTION: {deal_quality['objection']}")
    if deal_quality['deal_amount']:
        lines.append(f"DEAL AMOUNT: ${deal_quality['deal_amount']:,.0f}")
    if deal_quality['next_steps']:
        lines.append(f"NEXT STEP: {deal_quality['next_steps']}")
    if deal_quality['followup_date']:
        lines.append(f"FOLLOW-UP: {deal_quality['followup_date']}")

    return "\n".join(lines)


def sync_project(db, project_id):
    """Sync a single project from ProLine to local DB."""
    data = api_call("find/project", {"project_id": project_id})

    if not data.get('body'):
        print(f"  ❌ {project_id} — not found in ProLine")
        return False

    p = data['body'][0]
    current_notes = p.get('notes', '')
    current_hash = notes_hash(current_notes)

    # Check if notes changed since last sync
    last_hash = db.execute(
        "SELECT notes_hash FROM notes_history WHERE project_id = ? ORDER BY captured_at DESC LIMIT 1",
        (project_id,)
    ).fetchone()

    notes_changed = (last_hash is None) or (last_hash[0] != current_hash)

    if notes_changed and current_notes:
        # Store new notes snapshot
        db.execute(
            "INSERT INTO notes_history (project_id, notes_text, notes_hash, source) VALUES (?, ?, ?, ?)",
            (project_id, current_notes, current_hash, 'sync')
        )

    # Extract and archive any draft email
    draft = extract_draft_email(current_notes)
    if draft:
        existing = db.execute(
            "SELECT id FROM draft_emails WHERE project_id = ? AND subject = ? AND status = 'pending'",
            (project_id, draft['subject'])
        ).fetchone()
        if not existing:
            db.execute(
                "INSERT INTO draft_emails (project_id, contact_email, subject, body) VALUES (?, ?, ?, ?)",
                (project_id, draft['to'], draft['subject'], draft['body'])
            )

    # Update project record
    db.execute("""
        INSERT OR REPLACE INTO projects
        (project_id, project_number, project_name, stage, stage_id, status,
         address1, address2, city, state, zip, category, type,
         assigned_to_id, assigned_to_name, assigned_to_email, notes,
         quoted_value, approved_value, accounts_receivable,
         gross_revenue, net_revenue, gross_profit, gross_margin,
         merchant_fees, refunds, chargebacks,
         contact_id, contact_fname, contact_lname, contact_phone, contact_email,
         contact_lead_source, custom_field_1, custom_field_2, custom_field_3,
         custom_field_4, custom_field_5, custom_field_6, custom_field_7,
         updated_at, last_synced_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,
                datetime('now'), datetime('now'))
    """, (
        p['project_id'], p['project_number'], p['project_name'],
        p['stage'], p['stage_id'], p['status'],
        p['address1'], p['address2'], p['city'], p['state'], p['zip'],
        p['category'], p['type'],
        p['assigned_to_id'], p['assigned_to_name'], p['assigned_to_email'],
        current_notes,
        p['quoted_value'], p['approved_value'], p['accounts_receivable'],
        p['gross_revenue'], p['net_revenue'], p['gross_profit'], p['gross_margin'],
        p['merchant_fees'], p['refunds'], p['chargebacks'],
        p['contact_id'], p['contact_fname'], p['contact_lname'],
        p['contact_phone'], p['contact_email'], p['contact_lead_source'],
        p.get('custom_field_1', ''), p.get('custom_field_2', ''), p.get('custom_field_3', ''),
        p.get('custom_field_4', ''), p.get('custom_field_5', ''),
        p.get('custom_field_6', ''), p.get('custom_field_7', '')
    ))

    # Score deal quality
    dq = parse_deal_quality(current_notes)
    db.execute("""
        INSERT OR REPLACE INTO deal_quality
        (project_id, has_close_date, has_objection, has_deal_amount, has_next_steps,
         has_followup_date, score, grade, close_date, objection, deal_amount,
         next_steps, followup_date, scored_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))
    """, (
        project_id, dq['has_close_date'], dq['has_objection'], dq['has_deal_amount'],
        dq['has_next_steps'], dq['has_followup_date'], dq['score'], dq['grade'],
        dq['close_date'], dq['objection'], dq['deal_amount'],
        dq['next_steps'], dq['followup_date']
    ))

    # Sync associated events
    time.sleep(RATE_LIMIT_SECONDS)
    events_data = api_call("find/event", {"project_id": project_id})
    if events_data.get('body'):
        for e in events_data['body']:
            db.execute("""
                INSERT OR REPLACE INTO events
                (event_id, project_id, contact_id, type, duration,
                 start_date, end_date, time_zone, assignee_id, assignee_name,
                 external_id, updated_at, last_synced_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,datetime('now'),datetime('now'))
            """, (
                e['event_id'], e['project_id'], e['contact_id'],
                e['type'], e['duration'], e['start_date'], e['end_date'],
                e['time_zone'], e['assignee_id'], e['assignee_name'],
                e.get('external_id', '')
            ))

    changed = "📝 notes changed" if notes_changed else "no changes"
    print(f"  ✅ {p['project_name']} | {p['stage']} | Grade: {dq['grade']} | {changed}")
    return True


def main():
    if not PARTNER_KEY or not COMPANY_KEY:
        print("Missing PROLINE_PARTNER_KEY or PROLINE_COMPANY_KEY env vars.")
        print("Set them in .env or your shell before running.")
        return

    if not os.path.exists(DB_PATH):
        print(f"Local DB not found at {DB_PATH}.")
        print("Run `python3 scripts/init-db.py` first, then `python3 scripts/onboard.py`.")
        return

    db = sqlite3.connect(DB_PATH)
    start_time = datetime.now()

    print(f"PROLINE DAILY SYNC — {start_time.strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    # Get all known project IDs from local DB
    project_ids = [row[0] for row in db.execute("SELECT project_id FROM projects").fetchall()]

    if not project_ids:
        print("No projects in local DB. Nothing to sync.")
        db.close()
        return

    print(f"Syncing {len(project_ids)} projects ({RATE_LIMIT_SECONDS}s spacing)...\n")

    # Log sync start
    db.execute(
        "INSERT INTO sync_log (sync_type, project_count, status) VALUES (?, ?, ?)",
        ("daily", len(project_ids), "running")
    )
    sync_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.commit()

    success = 0
    for pid in project_ids:
        time.sleep(RATE_LIMIT_SECONDS)
        if sync_project(db, pid):
            success += 1
        db.commit()

    # Log sync complete
    db.execute(
        "UPDATE sync_log SET completed_at = datetime('now'), status = ? WHERE id = ?",
        (f"done — {success}/{len(project_ids)} synced", sync_id)
    )
    db.commit()

    # Print summary
    print()
    print("=" * 50)
    print(f"Sync complete: {success}/{len(project_ids)} projects")

    # Quick pipeline summary from local DB
    print()
    print("PIPELINE SUMMARY:")
    for row in db.execute("""
        SELECT p.status, COUNT(*) as cnt, SUM(p.quoted_value) as quoted,
               SUM(CASE WHEN d.grade IN ('C','F') THEN 1 ELSE 0 END) as needs_attention
        FROM projects p
        LEFT JOIN deal_quality d ON p.project_id = d.project_id
        GROUP BY p.status
    """):
        status, cnt, quoted, attention = row
        print(f"  {status}: {cnt} deals | ${quoted or 0:,.0f} quoted | {attention} need attention")

    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\nCompleted in {elapsed:.0f}s")

    db.close()


if __name__ == "__main__":
    main()
