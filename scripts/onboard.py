#!/usr/bin/env python3
"""
onboard.py — First-run wizard for proline-claw
Part of proline-claw (https://github.com/roofclaw/proline-claw)

Validates your ProLine credentials, discovers your tenant's stage IDs and
team member IDs, seeds your local SQLite DB with a starter batch of projects,
and writes a tenant-config.local.json file that other scripts and the skill
read at runtime.

Run once after cloning the repo and putting your keys in .env:
    python3 scripts/onboard.py

Safe to run again later if your tenant config changes (new reps, new stages).
"""

import json
import os
import subprocess
import sqlite3
import sys
import time
from datetime import datetime

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(REPO_ROOT, ".env")
DB_PATH = os.path.join(REPO_ROOT, "data", "proline.db")
CONFIG_PATH = os.path.join(REPO_ROOT, "data", "tenant-config.local.json")
BASE_URL = "https://api.proline.app/v1"
RATE_LIMIT_SECONDS = 6


def load_env_file(path):
    """Minimal .env loader — no dependency on python-dotenv."""
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip("'").strip('"')
            if k and k not in os.environ:
                os.environ[k] = v


def api_call(endpoint, payload, partner_key, company_key):
    result = subprocess.run([
        "curl", "-s", "-X", "POST", f"{BASE_URL}/{endpoint}",
        "-H", f"PARTNER_KEY: {partner_key}",
        "-H", f"COMPANY_KEY: {company_key}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload),
    ], capture_output=True, text=True)
    if result.returncode != 0:
        return {"error": f"curl failed: {result.stderr.strip()}"}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": result.stdout[:500]}


def prompt(msg, default=""):
    suffix = f" [{default}]" if default else ""
    val = input(f"{msg}{suffix}: ").strip()
    return val or default


def main():
    print("proline-claw onboarding")
    print("=" * 60)
    print()

    load_env_file(ENV_PATH)
    partner_key = os.environ.get("PROLINE_PARTNER_KEY", "")
    company_key = os.environ.get("PROLINE_COMPANY_KEY", "")

    if not partner_key or not company_key:
        print("Credentials missing.")
        print()
        print("Put your keys in .env (copy .env.example if you haven't):")
        print("  PROLINE_PARTNER_KEY=...")
        print("  PROLINE_COMPANY_KEY=...")
        print()
        print("Need a partner key? See docs/partner-key-request.md")
        sys.exit(1)

    if not os.path.exists(DB_PATH):
        print(f"Local DB not found at {DB_PATH}")
        print("Run `python3 scripts/init-db.py` first, then re-run onboarding.")
        sys.exit(1)

    # --- Step 1: validate keys by looking up a team member ---
    print("Step 1: validate credentials")
    print("-" * 60)
    your_email = prompt("What's the email address of a team member in your ProLine tenant?")
    if not your_email:
        print("Aborting: need a team member email to verify credentials.")
        sys.exit(1)

    tm = api_call("find/team_member", {"user_email": your_email}, partner_key, company_key)
    if tm.get("error") or tm.get("statusCode", 200) >= 400:
        print("ProLine rejected the request.")
        print(f"Response: {json.dumps(tm, indent=2)[:500]}")
        print()
        print("Common causes:")
        print("  - PARTNER_KEY and COMPANY_KEY swapped (partner is the integrator key)")
        print("  - Email doesn't match a team member in this ProLine tenant")
        print("  - Partner key not yet approved by ProLine")
        sys.exit(1)

    body = tm.get("body")
    if not body:
        print(f"No team member found with email {your_email}.")
        print("Double-check the email in ProLine and try again.")
        sys.exit(1)

    rep = body[0] if isinstance(body, list) else body
    default_rep_user_id = rep.get("user_id", "")
    default_rep_name = rep.get("name", "")
    print(f"  Authenticated. Found rep: {default_rep_name} ({default_rep_user_id})")
    print()

    # --- Step 2: discover stage IDs from existing projects ---
    print("Step 2: discover your tenant's stage IDs")
    print("-" * 60)
    print("Enter a few project IDs from your ProLine tenant (one per line, blank to stop).")
    print("These are used to discover your stage IDs. Find them in the ProLine UI URL bar.")
    print("If you have none yet, press enter — we'll skip this step.")

    project_ids = []
    while True:
        pid = input("  project_id: ").strip()
        if not pid:
            break
        project_ids.append(pid)

    stages_discovered = {}
    reps_discovered = {}
    projects_seeded = 0

    if project_ids:
        print(f"\nFetching {len(project_ids)} project(s) (rate limit: {RATE_LIMIT_SECONDS}s spacing)...")
        db = sqlite3.connect(DB_PATH)
        for pid in project_ids:
            time.sleep(RATE_LIMIT_SECONDS)
            resp = api_call("find/project", {"project_id": pid}, partner_key, company_key)
            if resp.get("error") or not resp.get("body"):
                print(f"  Could not fetch {pid} — skipping")
                continue
            proj = resp["body"][0] if isinstance(resp["body"], list) else resp["body"]

            stage = proj.get("stage", "")
            stage_id = proj.get("stage_id", "")
            if stage and stage_id:
                stages_discovered[stage] = stage_id

            rep_id = proj.get("assigned_to_id", "")
            rep_email = proj.get("assigned_to_email", "")
            rep_name = proj.get("assigned_to_name", "")
            if rep_id and rep_email:
                reps_discovered[rep_email] = {"name": rep_name, "email": rep_email, "user_id": rep_id}

            # Seed into local DB
            db.execute("""
                INSERT OR REPLACE INTO projects
                (project_id, project_number, project_name, stage, stage_id, status,
                 address1, address2, city, state, zip, category, type,
                 assigned_to_id, assigned_to_name, assigned_to_email, notes,
                 quoted_value, approved_value, accounts_receivable,
                 gross_revenue, net_revenue, gross_profit, gross_margin,
                 merchant_fees, refunds, chargebacks,
                 contact_id, contact_fname, contact_lname, contact_phone, contact_email,
                 contact_lead_source, last_synced_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))
            """, (
                proj.get("project_id"), proj.get("project_number"), proj.get("project_name"),
                proj.get("stage"), proj.get("stage_id"), proj.get("status"),
                proj.get("address1"), proj.get("address2"), proj.get("city"),
                proj.get("state"), proj.get("zip"), proj.get("category"), proj.get("type"),
                proj.get("assigned_to_id"), proj.get("assigned_to_name"), proj.get("assigned_to_email"),
                proj.get("notes"),
                proj.get("quoted_value", 0), proj.get("approved_value", 0),
                proj.get("accounts_receivable", 0), proj.get("gross_revenue", 0),
                proj.get("net_revenue", 0), proj.get("gross_profit", 0), proj.get("gross_margin", 0),
                proj.get("merchant_fees", 0), proj.get("refunds", 0), proj.get("chargebacks", 0),
                proj.get("contact_id"), proj.get("contact_fname"), proj.get("contact_lname"),
                proj.get("contact_phone"), proj.get("contact_email"), proj.get("contact_lead_source"),
            ))
            projects_seeded += 1
            print(f"  Seeded: {proj.get('project_name')} ({stage})")
        db.commit()
        db.close()
    else:
        print("  Skipped. You can seed later by running daily-sync.py once you have project IDs.")
    print()

    # --- Step 3: write tenant-config.local.json ---
    print("Step 3: write tenant config")
    print("-" * 60)

    # Let user label common stages
    leads_stage_id = ""
    appt_stage_id = ""
    if stages_discovered:
        print("Stages discovered:")
        for stage, sid in stages_discovered.items():
            print(f"  {stage}: {sid}")
        print()
        leads_stage_id = prompt("Which of the above stage IDs is your LEADS stage? (paste ID, or leave blank)")
        appt_stage_id = prompt("Which of the above stage IDs is your APPT SCHEDULED stage? (paste ID, or leave blank)")

    config = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "default_rep_user_id": default_rep_user_id,
        "default_rep_name": default_rep_name,
        "default_rep_email": your_email,
        "leads_stage_id": leads_stage_id,
        "appt_scheduled_stage_id": appt_stage_id,
        "all_discovered_stages": stages_discovered,
        "reps": list(reps_discovered.values()) or [
            {"name": default_rep_name, "email": your_email, "user_id": default_rep_user_id}
        ],
    }

    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    print(f"  Wrote {CONFIG_PATH}")
    print()

    # --- Done ---
    print("Onboarding complete")
    print("=" * 60)
    print(f"Rep confirmed:          {default_rep_name} <{your_email}>")
    print(f"Projects seeded:        {projects_seeded}")
    print(f"Stages discovered:      {len(stages_discovered)}")
    print(f"Additional reps found:  {max(0, len(reps_discovered) - 1)}")
    print()
    print("Next steps:")
    print("  1. Run `python3 scripts/daily-sync.py` to refresh the DB with latest data.")
    print("  2. Schedule daily-sync.py for 5am via cron or your scheduler.")
    print("  3. Schedule weather-check.py evening (9pm) and morning (5am) if you want the rain-day engine.")
    print("  4. Point your OpenClaw / RoofClaw agent at skills/SKILL.md.")
    print()
    print("Keep .env and data/tenant-config.local.json out of git — the provided .gitignore handles this.")


if __name__ == "__main__":
    main()
