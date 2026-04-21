# Rain Day Decision Engine — Design Document

## The Problem

Roofing production managers wake up at 5am to check weather and decide whether to run or cancel jobs. Wrong calls cost thousands:

- **Not calling soon enough:** Legal liability — some states require notice by a certain time or you owe 4 hours wages per worker. 10 crews × 6 guys × $25/hr × 4 hrs = **$6,000 wasted**.
- **Calling unnecessarily:** Lost production day, pushed schedule, frustrated customers.
- **Not calling when you should:** Exposed roof + rainstorm = water damage = insurance claim or out-of-pocket repair. **$10,000+ per incident.**
- **Cascading calendar chaos:** Every rain day pushes the entire schedule forward. Skip weekends. Fill Saturdays. Customers get frustrated. Crews lose income.

## The Solution

The agent monitors weather overnight and makes a go/no-go recommendation (or decision, as trust builds) before 5am, then executes the communication cascade automatically.

---

## Decision Timeline

```
9:00 PM (night before)
  └─ EVENING CHECK
     - Pull tomorrow's job list from ProLine events + local DB
     - Geocode all job addresses
     - Get hourly forecast for each location
     - Assess initial risk level
     - Log trend baseline
     - If HIGH risk: send early warning to production manager
       "Heads up — tomorrow's looking wet. I'll have a final call at 5am."

5:00 AM (morning of)
  └─ MORNING DECISION
     - Re-pull hourly forecast for all job locations
     - Compare to last night's forecast (trend analysis)
     - Apply rubric to each job individually (different locations may have different weather)
     - Generate decision: GO / CALL / PARTIAL (some jobs go, some don't)
     - Present to production manager with reasoning
     
     If SEMI-AUTO (early trust):
       "Here's my recommendation. Reply GO or CALL to confirm."
     
     If FULL-AUTO (established trust):
       Execute immediately, notify manager of actions taken.

5:15 AM (if CALL)
  └─ NOTIFICATION CASCADE
     1. Notify subcontractors — "Day called due to weather. Do not report."
     2. Notify customers — "Your install has been rescheduled due to weather."
     3. Reschedule jobs — shift calendar forward, skip weekends
     4. Update ProLine project notes
     5. Log rain day in tracking table

6:00 AM (if PARTIAL CALL)
  └─ SELECTIVE EXECUTION
     - Some crews go, some don't (based on job location weather)
     - Targeted notifications only to affected crews/customers
```

---

## Decision Rubric (Configurable)

Default thresholds — production manager can adjust:

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Precipitation probability | ≥ 50% during work hours (7am-5pm) | FLAG |
| Precipitation amount | ≥ 5mm during work hours | FLAG |
| Wind speed | ≥ 40 km/h (25 mph) sustained | FLAG |
| Combined: probability ≥ 50% AND amount ≥ 5mm | — | CALL recommended |
| Combined: wind ≥ 40 km/h for 3+ consecutive hours | — | CALL recommended |
| Precipitation ≥ 70% AND amount ≥ 10mm | — | AUTO-CALL (full trust mode) |

**Work hours window:** 7:00 AM - 5:00 PM local time at job site

**Trend factor:** If last night's forecast showed 30% rain and morning shows 60%, the trend is worsening → weight toward CALL. If last night showed 70% and morning shows 40%, trend is improving → weight toward GO.

---

## Technical Architecture

### Data Sources (All Free, No API Keys)

| Source | What It Provides | Cost |
|--------|-----------------|------|
| **Open-Meteo API** | Hourly precipitation %, amount (mm), wind speed, weather codes | Free |
| **Nominatim (OSM)** | Address → lat/lon geocoding | Free |
| **ProLine events** | Tomorrow's scheduled jobs with addresses | Existing API |
| **Local SQLite** | Job history, rain day tracking, crew schedules | Local |

### New SQLite Tables

```sql
CREATE TABLE weather_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_type TEXT,           -- 'evening' or 'morning'
    check_date DATE,           -- the date being checked (tomorrow)
    project_id TEXT,
    job_address TEXT,
    latitude REAL,
    longitude REAL,
    precip_prob_max INTEGER,   -- max probability during work hours
    precip_total_mm REAL,      -- total precipitation during work hours
    wind_max_kmh REAL,         -- max wind during work hours
    risk_level TEXT,           -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    decision TEXT,             -- 'GO', 'CALL', 'PENDING'
    trend_vs_evening TEXT,     -- 'IMPROVING', 'STABLE', 'WORSENING'
    raw_hourly_json TEXT,      -- full hourly data for audit
    checked_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rain_days (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rain_date DATE,
    decision TEXT,             -- 'FULL_CALL', 'PARTIAL_CALL'
    affected_projects TEXT,    -- JSON array of project_ids
    affected_crews INTEGER,
    estimated_cost REAL,       -- estimated cost of the rain day
    notifications_sent INTEGER,
    rescheduled_count INTEGER,
    decided_at DATETIME,
    decided_by TEXT            -- 'agent_auto', 'agent_recommendation', 'manager_override'
);

CREATE TABLE geocode_cache (
    address TEXT PRIMARY KEY,
    latitude REAL,
    longitude REAL,
    display_name TEXT,
    cached_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## Cron Schedule

```
9:00 PM EST — Evening weather check
  → Query tomorrow's events from ProLine
  → Geocode addresses (cache results)
  → Pull Open-Meteo forecast for each location
  → Score risk level
  → If HIGH: send early warning to production manager
  → Store in weather_checks table

5:00 AM EST — Morning decision
  → Re-pull forecast for all locations
  → Compare to evening check (trend analysis)
  → Apply rubric
  → Generate decision + reasoning
  → Send to production manager (or auto-execute in full trust mode)

5:15 AM EST — Execute (if CALL confirmed)
  → Notification cascade
  → Calendar rescheduling
  → Update ProLine notes
  → Log rain day
```

---

## Communication Templates

### Early Warning (9pm)
```
🌧️ WEATHER ALERT — Tomorrow may be a rain day.

Current forecast for [DATE]:
- [LOCATION 1]: [X]% chance of rain, [Y]mm expected, wind [Z] km/h
- [LOCATION 2]: [X]% chance of rain, [Y]mm expected, wind [Z] km/h

I'll have a final decision at 5am. No action needed from you right now.
```

### Morning Decision — Recommend CALL
```
🔴 RAIN DAY RECOMMENDATION — [DATE]

[X] jobs scheduled today. Weather doesn't look good:
- [LOCATION 1]: [X]% rain, [Y]mm, wind [Z] km/h — CALL
- [LOCATION 2]: [X]% rain, [Y]mm, wind [Z] km/h — CALL
- [LOCATION 3]: [X]% rain, [Y]mm, wind [Z] km/h — borderline

Trend since last night: [WORSENING/STABLE]

My recommendation: CALL THE DAY

Reply CALL to confirm and I'll notify [X] subs and [Y] customers and reschedule.
Reply GO to override.
Reply PARTIAL to discuss which jobs to keep.
```

### Morning Decision — GO
```
✅ WEATHER CHECK — [DATE]

All clear for today's jobs:
- [LOCATION 1]: [X]% rain, [Y]mm — GO
- [LOCATION 2]: [X]% rain, [Y]mm — GO

All crews should report as scheduled.
```

### Sub Notification
```
[Crew/Sub Name] — Weather call for [DATE].
Do not report to [JOB ADDRESS] tomorrow. 
Rescheduled to [NEW DATE]. We'll confirm the night before.
— [Your Roofing Co.]
```

### Customer Notification
```
Hi [CUSTOMER NAME],

Due to weather conditions, we need to reschedule your roof installation 
originally planned for [DATE]. Your new date is [NEW DATE].

We know this is frustrating and we apologize for the inconvenience. 
We'd rather wait for safe conditions than risk any issues with your roof.

We'll confirm the night before your new date. If you have any questions, 
don't hesitate to reach out.

— [Your Roofing Co.]
```

---

## Calendar Rescheduling Logic

```
When a day is CALLED:

1. Get all jobs scheduled for that day
2. For each job:
   a. Find the next available workday (skip weekends unless catch-up needed)
   b. If this is the 2nd+ consecutive rain day:
      - Consider Saturday as available (catch-up mode)
      - Flag for production manager approval
   c. Move the job to the new date
   d. Push all subsequent jobs for that crew forward by 1 day
   e. Skip weekends in the cascade unless catch-up mode

3. Track consecutive rain days per crew
   - 1 rain day: shift to next workday
   - 2 consecutive: suggest Saturday catch-up
   - 3+ consecutive: flag as critical — crews losing income,
     schedule is significantly behind, may need weekend work

4. Update ProLine events via events/edit
5. Update project notes with reschedule reason
6. Customer notification includes new date
```

---

## Rain Day Cost Tracking

```
Per rain day:
  crews_affected × workers_per_crew × hourly_rate × penalty_hours = liability_if_late
  
  Example: 10 crews × 6 workers × $25/hr × 4 hrs = $6,000

Track cumulative:
  - Rain days this month / this year
  - Total estimated cost of rain days
  - Catch-up days worked (Saturdays)
  - Average reschedule delay
```

---

## Trust Levels

| Level | Behavior | When |
|-------|----------|------|
| **Monitor only** | Report weather, no recommendations | Week 1 |
| **Semi-auto** | Recommend GO/CALL, wait for confirmation | Weeks 2-4 |
| **Full-auto** | Make the call, execute notifications, report actions | Month 2+ |

Production manager can override at any time. All decisions logged for review.

---

## Implementation Phases

### Phase 1: Weather Monitoring (NOW — no external deps)
- Pull tomorrow's events from local DB
- Geocode addresses (Nominatim, cached)
- Get Open-Meteo forecast
- Score risk
- Send evening + morning reports to production manager
- **No action taken — monitoring only**

### Phase 2: Decision Engine (After trust builds)
- Apply rubric
- Trend analysis (evening vs morning)
- Recommend GO/CALL/PARTIAL
- Wait for confirmation before acting

### Phase 3: Full Automation (When trusted)
- Auto-execute notification cascade
- Auto-reschedule calendar
- Auto-notify subs and customers
- Log everything, report actions taken

---

## Dependencies

| Dependency | Status | Needed For |
|-----------|--------|------------|
| Open-Meteo API | ✅ Tested, working | Weather data |
| Nominatim geocoding | ✅ Tested, working | Address → lat/lon |
| ProLine events API | ✅ Working | Tomorrow's job list |
| ProLine events/edit | ✅ Working | Rescheduling |
| ProLine edit/project | ✅ Working | Updating notes |
| Sub contact list | ❌ Not yet built | Notifying subs |
| Customer notification method | ❌ TBD | Notifying customers |
| Cron jobs | ✅ Available via OpenClaw | Scheduling checks |
| Local SQLite | ✅ Built | Tracking everything |
