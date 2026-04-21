#!/usr/bin/env python3
"""
weather-check.py — Rain Day Decision Engine
Part of proline-claw (https://github.com/Roofing-Business-Partner/proline-claw)

Checks weather for tomorrow's scheduled jobs and scores risk.
Run twice: evening (9pm) and morning (5am).

Usage:
    python3 weather-check.py evening    # 9pm check
    python3 weather-check.py morning    # 5am check

Requires env vars:
    PROLINE_PARTNER_KEY
    PROLINE_COMPANY_KEY
"""

import json
import subprocess
import sqlite3
import os
import sys
import time
from datetime import datetime, timedelta
from urllib.parse import quote

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "proline.db")
PARTNER_KEY = os.environ.get("PROLINE_PARTNER_KEY", "")
COMPANY_KEY = os.environ.get("PROLINE_COMPANY_KEY", "")

# --- Configurable Rubric ---
RUBRIC = {
    "precip_prob_threshold": 50,      # % probability to flag
    "precip_mm_threshold": 5,         # mm to flag
    "wind_kmh_threshold": 40,         # km/h to flag
    "auto_call_prob": 70,             # % probability for auto-call
    "auto_call_mm": 10,               # mm for auto-call
    "work_hour_start": 7,             # 7am
    "work_hour_end": 17,              # 5pm
}


def api_call(endpoint, payload):
    result = subprocess.run([
        'curl', '-s', '-X', 'POST', f'https://api.proline.app/v1/{endpoint}',
        '-H', f'PARTNER_KEY: {PARTNER_KEY}',
        '-H', f'COMPANY_KEY: {COMPANY_KEY}',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps(payload)
    ], capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        return {"error": result.stdout}


def geocode(address, db):
    """Geocode an address, using cache when available."""
    cached = db.execute(
        "SELECT latitude, longitude FROM geocode_cache WHERE address = ?",
        (address,)
    ).fetchone()
    if cached:
        return cached[0], cached[1]

    encoded = quote(address)
    result = subprocess.run([
        'curl', '-s',
        f'https://nominatim.openstreetmap.org/search?q={encoded}&format=json&limit=1',
        '-H', 'User-Agent: proline-claw/1.0'
    ], capture_output=True, text=True)

    try:
        data = json.loads(result.stdout)
        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            db.execute(
                "INSERT OR REPLACE INTO geocode_cache (address, latitude, longitude, display_name) VALUES (?,?,?,?)",
                (address, lat, lon, data[0].get('display_name', ''))
            )
            db.commit()
            return lat, lon
    except:
        pass

    return None, None


def get_forecast(lat, lon, target_date):
    """Get hourly forecast from Open-Meteo for a specific location."""
    result = subprocess.run([
        'curl', '-s',
        f'https://api.open-meteo.com/v1/forecast?'
        f'latitude={lat}&longitude={lon}'
        f'&hourly=precipitation_probability,precipitation,wind_speed_10m,weather_code'
        f'&daily=precipitation_sum,precipitation_probability_max,wind_speed_10m_max'
        f'&timezone=auto&forecast_days=3'
    ], capture_output=True, text=True)

    try:
        data = json.loads(result.stdout)
        target_str = target_date.strftime('%Y-%m-%d')

        # Extract work-hours data for target date
        hourly = data['hourly']
        work_hours = []
        for i, t in enumerate(hourly['time']):
            if target_str in t:
                hour = int(t.split('T')[1].split(':')[0])
                if RUBRIC['work_hour_start'] <= hour <= RUBRIC['work_hour_end']:
                    work_hours.append({
                        'time': t,
                        'precip_prob': hourly['precipitation_probability'][i],
                        'precip_mm': hourly['precipitation'][i],
                        'wind_kmh': hourly['wind_speed_10m'][i],
                        'weather_code': hourly['weather_code'][i]
                    })

        if not work_hours:
            return None

        return {
            'hourly': work_hours,
            'precip_prob_max': max(h['precip_prob'] for h in work_hours),
            'precip_total_mm': sum(h['precip_mm'] for h in work_hours),
            'wind_max_kmh': max(h['wind_kmh'] for h in work_hours),
            'raw': data
        }
    except Exception as e:
        print(f"  Weather API error: {e}")
        return None


def score_risk(forecast):
    """Score risk level based on rubric."""
    prob = forecast['precip_prob_max']
    mm = forecast['precip_total_mm']
    wind = forecast['wind_max_kmh']

    if (prob >= RUBRIC['auto_call_prob'] and mm >= RUBRIC['auto_call_mm']) or wind >= 60:
        return 'CRITICAL', 'CALL'
    elif (prob >= RUBRIC['precip_prob_threshold'] and mm >= RUBRIC['precip_mm_threshold']) or wind >= RUBRIC['wind_kmh_threshold']:
        return 'HIGH', 'CALL'
    elif prob >= RUBRIC['precip_prob_threshold'] or mm >= 3 or wind >= 30:
        return 'MEDIUM', 'PENDING'
    else:
        return 'LOW', 'GO'


def get_trend(db, project_id, check_date):
    """Compare current check against evening check for trend analysis."""
    evening = db.execute(
        "SELECT precip_prob_max, precip_total_mm FROM weather_checks "
        "WHERE project_id = ? AND check_date = ? AND check_type = 'evening' "
        "ORDER BY checked_at DESC LIMIT 1",
        (project_id, check_date)
    ).fetchone()

    if not evening:
        return 'NO_BASELINE'

    return None  # Will be set after comparison


def main():
    check_type = sys.argv[1] if len(sys.argv) > 1 else 'morning'
    if check_type not in ('evening', 'morning'):
        print("Usage: python3 weather-check.py [evening|morning]")
        return

    db = sqlite3.connect(DB_PATH)
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    tomorrow_str = tomorrow.strftime('%Y-%m-%d')

    print(f"{'🌙 EVENING' if check_type == 'evening' else '☀️ MORNING'} WEATHER CHECK — {tomorrow_str}")
    print("=" * 60)

    # Get all projects with events tomorrow from local DB
    # Also check projects that have events from ProLine
    projects = db.execute("""
        SELECT DISTINCT p.project_id, p.project_name, p.address1, p.city, p.state, p.zip,
               p.assigned_to_name, p.contact_fname, p.contact_lname, p.contact_phone
        FROM projects p
        LEFT JOIN events e ON p.project_id = e.project_id
        WHERE p.status NOT IN ('Closed', 'Lost', 'Disqualified')
    """).fetchall()

    if not projects:
        print("No active projects found in local DB.")
        db.close()
        return

    print(f"Checking weather for {len(projects)} active projects...\n")

    results = []
    for proj in projects:
        pid, name, addr1, city, state, zip_code, rep, cfname, clname, cphone = proj
        full_address = f"{addr1}, {city}, {state} {zip_code}"

        # Geocode
        lat, lon = geocode(full_address, db)
        if lat is None:
            print(f"  ⚠️ {name}: Could not geocode {full_address}")
            continue

        # Get forecast
        time.sleep(1)  # Rate limit Nominatim
        forecast = get_forecast(lat, lon, tomorrow)
        if not forecast:
            print(f"  ⚠️ {name}: Could not get forecast")
            continue

        # Score risk
        risk, decision = score_risk(forecast)

        # Check trend (morning only)
        trend = 'N/A'
        if check_type == 'morning':
            evening = db.execute(
                "SELECT precip_prob_max, precip_total_mm, wind_max_kmh FROM weather_checks "
                "WHERE project_id = ? AND check_date = ? AND check_type = 'evening' "
                "ORDER BY checked_at DESC LIMIT 1",
                (pid, tomorrow_str)
            ).fetchone()
            if evening:
                prob_diff = forecast['precip_prob_max'] - evening[0]
                if prob_diff > 10:
                    trend = 'WORSENING'
                elif prob_diff < -10:
                    trend = 'IMPROVING'
                else:
                    trend = 'STABLE'

        # Store
        db.execute("""
            INSERT INTO weather_checks
            (check_type, check_date, project_id, job_address, latitude, longitude,
             precip_prob_max, precip_total_mm, wind_max_kmh, risk_level, decision,
             trend_vs_evening, raw_hourly_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            check_type, tomorrow_str, pid, full_address, lat, lon,
            forecast['precip_prob_max'], forecast['precip_total_mm'],
            forecast['wind_max_kmh'], risk, decision, trend,
            json.dumps(forecast['hourly'])
        ))

        icon = {'LOW': '✅', 'MEDIUM': '🟡', 'HIGH': '🔴', 'CRITICAL': '⛔'}[risk]
        results.append({
            'name': name, 'address': full_address, 'risk': risk, 'decision': decision,
            'prob': forecast['precip_prob_max'], 'mm': forecast['precip_total_mm'],
            'wind': forecast['wind_max_kmh'], 'trend': trend, 'icon': icon,
            'rep': rep, 'contact': f"{cfname} {clname}", 'phone': cphone
        })
        print(f"  {icon} {name} ({city}, {state})")
        print(f"     Rain: {forecast['precip_prob_max']}% / {forecast['precip_total_mm']:.1f}mm | Wind: {forecast['wind_max_kmh']:.0f} km/h | Risk: {risk} | {decision}")
        if check_type == 'morning' and trend != 'N/A':
            print(f"     Trend since last night: {trend}")
        print()

    db.commit()

    # Summary
    print("=" * 60)
    call_jobs = [r for r in results if r['decision'] == 'CALL']
    go_jobs = [r for r in results if r['decision'] == 'GO']
    pending_jobs = [r for r in results if r['decision'] == 'PENDING']

    print(f"SUMMARY: {len(go_jobs)} GO | {len(pending_jobs)} PENDING | {len(call_jobs)} CALL")

    if call_jobs:
        print(f"\n🔴 RECOMMENDED TO CALL:")
        for j in call_jobs:
            print(f"   - {j['name']} ({j['prob']}% rain, {j['mm']:.1f}mm, {j['wind']:.0f}km/h wind)")

    if pending_jobs:
        print(f"\n🟡 BORDERLINE — NEEDS JUDGMENT:")
        for j in pending_jobs:
            print(f"   - {j['name']} ({j['prob']}% rain, {j['mm']:.1f}mm, {j['wind']:.0f}km/h wind)")

    db.close()
    print(f"\nCheck complete. Results stored in weather_checks table.")


if __name__ == "__main__":
    main()
