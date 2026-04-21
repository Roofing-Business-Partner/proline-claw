# ProLine Webhooks — Reference & Integration Design

Source: https://help.proline.app/en/articles/12707242-proline-webhooks
Scraped: 2026-03-09

---

## Overview

ProLine webhooks are **outbound only** — they push JSON payloads to a destination URL when events occur. No retry guarantees, no two-way communication.

---

## Webhook Triggers Available

| Trigger | What Fires It |
|---------|--------------|
| **Project Created** | New project added to ProLine |
| **Project Created or Updated** | Any project create or edit |
| **Quote Sent or Approved** | Quote emailed to customer or signed |
| **Invoice Sent or Approved** | Invoice emailed or paid |

**Stage Filter:** Project-based triggers can be filtered to only fire for specific stages.

---

## Payload Schemas

### Project Payload (on create/update)
```json
{
  "project_name": "string",
  "project_number": "string",
  "project_id": "string",
  "location": "string",
  "area": "string",
  "type": "string",
  "category": "string",
  "services": "string",
  "tags": "string",
  "status": "string",
  "stage": "string",
  "stage_id": "string",
  "address1": "string",
  "address2": "string",
  "city": "string",
  "state": "string",
  "zip": "string",
  "assigned_to_id": "string",
  "assigned_to_email": "string",
  "assigned_to_name": "string",
  "notes": "string",
  "contact_id": "string",
  "contact_fname": "string",
  "contact_lname": "string",
  "contact_phone": "string",
  "contact_email": "string"
}
```

### Quote Payload
```json
{
  "project_name": "string",
  "project_number": "string",
  "project_id": "string",
  "quote_name": "string",
  "quote_id": "string",
  "share_link": "string",
  "pdf_doc": "string",
  "status": "string",
  "sent_date": "string",
  "approved_date": "string",
  "approved_total": "string"
}
```

### Invoice Payload
```json
{
  "project_name": "string",
  "project_number": "string",
  "project_id": "string",
  "invoice_name": "string",
  "invoice_number": "string",
  "invoice_id": "string",
  "type": "string",
  "status": "string",
  "share_link": "string",
  "pdf_doc": "string",
  "total": "string",
  "amount_due": "string",
  "balance": "string",
  "sent_date": "string",
  "paid_date": "string"
}
```

---

## What This Means for proline-claw

### The Project Webhook Solves Our Registry Problem
The "Project Created" webhook sends us the `project_id`, full contact info, stage, and notes — everything we need to add a project to our local DB. We no longer have to discover projects through the API.

### The Quote Webhook Solves Our Financial Data Problem
Since we can't write `quoted_value` via the API, we rely on ProLine's quoting UI. But the Quote webhook sends us:
- `approved_total` — the signed contract value
- `share_link` — link to the quote
- `pdf_doc` — the actual PDF
- `sent_date` / `approved_date`

This is how we get financial data without polling.

### The Invoice Webhook Completes the Revenue Picture
- `total`, `amount_due`, `balance`
- `sent_date`, `paid_date`
- Revenue, AR, and payment tracking — all pushed to us automatically.

---

## Integration Architecture

### Recommended: Make.com as Middleware

```
ProLine Webhook → Make.com Scenario → Agent (Telegram/Slack/email message)
```

**Setup in ProLine:**
1. Go to Integrations → API → Webhooks
2. Add 3 webhooks:
   - Trigger: "Project Created or Updated" → URL: Make.com webhook URL
   - Trigger: "Quote Sent or Approved" → URL: Make.com webhook URL
   - Trigger: "Invoice Sent or Approved" → URL: Make.com webhook URL

**Setup in Make.com:**
1. Webhook trigger receives ProLine payload
2. Format a structured message
3. Send to your agent via Telegram / Slack / email — whichever channel your harness watches

**Message format from Make.com to the agent:**
```
PROLINE_WEBHOOK: PROJECT_UPDATE
project_id: <tenant-specific project id>
project_name: <project name>
stage: APPT SCHEDULED
contact_id: <tenant-specific contact id>
contact_name: <contact name>
contact_email: <contact email>
```

```
PROLINE_WEBHOOK: QUOTE_APPROVED
project_id: <tenant-specific project id>
quote_id: ...
approved_total: 22000
share_link: https://...
```

```
PROLINE_WEBHOOK: INVOICE_PAID
project_id: <tenant-specific project id>
invoice_id: ...
total: 22000
paid_date: 03/25/2026
balance: 0
```

**Agent's response:**
1. Parse the structured message
2. Upsert into local SQLite DB
3. Update deal quality score
4. If new project → full sync from API to get complete data
5. Acknowledge with a brief confirmation (or NO_REPLY if routine)

---

## New SQLite Tables Needed

### quotes
```sql
CREATE TABLE quotes (
    quote_id TEXT PRIMARY KEY,
    project_id TEXT,
    quote_name TEXT,
    share_link TEXT,
    pdf_doc TEXT,
    status TEXT,
    sent_date TEXT,
    approved_date TEXT,
    approved_total REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
```

### invoices
```sql
CREATE TABLE invoices (
    invoice_id TEXT PRIMARY KEY,
    project_id TEXT,
    invoice_name TEXT,
    invoice_number TEXT,
    type TEXT,
    status TEXT,
    share_link TEXT,
    pdf_doc TEXT,
    total REAL,
    amount_due REAL,
    balance REAL,
    sent_date TEXT,
    paid_date TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
```

---

## Limitations

- **No retry guarantee** — if Make.com or Telegram is down, the webhook may be lost
- **One-way only** — can't write back to ProLine via webhook
- **Payloads may evolve** — field names could change over time
- **Timing** — webhook may fire before other ProLine workflow steps complete
- **Duplicates possible** — need to handle gracefully (upsert, not insert)

---

## Setup Checklist

- [ ] Create / access a Make.com account (free tier is fine for low volume)
- [ ] Create 3 Make.com scenarios (project, quote, invoice)
- [ ] Configure ProLine webhooks → Make.com webhook URLs
- [ ] Configure Make.com → agent notification channel (Telegram, Slack, email, etc.)
- [ ] Agent parses structured messages and updates SQLite
- [ ] Test end-to-end with a manual project create in ProLine
