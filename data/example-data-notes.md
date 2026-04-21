# data/example.db — what "good" looks like

`example.db` is a demo SQLite database seeded with a fictional roofing company called **ExampleCo Roofing**. It's included so you can see what a well-instrumented ProLine tenant looks like after the skill has been running for a while — real pipeline, graded deals, a follow-up queue, weather checks, and a sync log.

**Nothing in `example.db` is real.** All names, addresses, emails, phone numbers, and ID values are fabricated. Safe to share, safe to fork, safe to delete.

---

## What's in it

### Projects (6)

| Project | Stage | Status | Grade | Why the grade |
|---|---|---|---|---|
| Alex Morgan | QUOTED | Open | **A** | Full inspection notes, objection captured, price quoted, follow-up staged, draft email ready |
| Jamie Rivera | APPT SCHEDULED | Inspection | **C** | Has objection + next step, but no quoted amount yet (inspection tomorrow) |
| Sam Chen | LEADS | Lead | **F** | Minimal notes, no inspection booked |
| Riley Thomas | LEADS | Lead | **F** | No notes at all — the kind of deal that slips through the cracks |
| Taylor Brooks | JOB WON | Won | **C** | Contract signed and deposit paid — financial fields populated via webhook |
| Casey Park | LOST SALE | Lost | **C** | Lost reason recorded; useful for win/loss analysis |

### Events (2)
- Tomorrow 2pm — inspection with Jamie Rivera (assigned: Pat Smith)
- Next Wednesday 10am — follow-up call with Alex Morgan (assigned: Jordan Lee)

### Deal quality (6)
Scored on 5 signals: close date, objection, deal amount, next steps, follow-up date. A = 5/5, F = 0/5.

### Weather checks (3)
Two mornings/evenings of Open-Meteo + Nominatim output. One "CALL" decision triggered by 65% rain probability + 8.5mm forecast.

### Reps
- **Pat Smith** (pat@examplecoroofing.com) — owner/primary
- **Jordan Lee** (jordan@examplecoroofing.com) — sales

### Stages
- LEADS / APPT SCHEDULED / QUOTED / JOB WON / LOST SALE

---

## Using it as a reference

1. **To browse the demo:**
   ```bash
   sqlite3 data/example.db
   .tables
   SELECT project_name, stage, grade FROM projects p
   JOIN deal_quality d ON p.project_id = d.project_id;
   ```

2. **To study the notes format:** open Alex Morgan's record — it's the reference shape for how the skill expects `project_notes` to be structured (inspection block + draft email block).

3. **To preview the rain-day engine output:** `SELECT * FROM weather_checks ORDER BY check_date, check_type;`

---

## Replacing it with your own data

The demo is read-only in spirit — don't sync against it. Start your own DB:

```bash
# 1. Ensure the example isn't your working DB (it shouldn't be — scripts write to proline.db)
ls data/

# 2. Initialize your own DB
python3 scripts/init-db.py

# 3. Onboard (validates keys, discovers your stage IDs, seeds first projects)
python3 scripts/onboard.py
```

Your live data lives in `data/proline.db` (gitignored). The example stays put for reference.

If you want a fresh example for demo purposes (e.g. showing a client) you can re-copy:
```bash
cp data/example.db data/proline.db
```
…but remember to wipe and re-onboard when you're ready to go live.
