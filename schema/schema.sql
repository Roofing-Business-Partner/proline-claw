-- proline-claw — SQLite schema
-- All 15 tables used by scripts/daily-sync.py, scripts/weather-check.py,
-- and the pipeline reporting workflow.
--
-- Initialize with: python3 scripts/init-db.py

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------
-- Core ProLine mirrors (synced by daily-sync.py)
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    project_number TEXT,
    project_name TEXT,
    stage TEXT,
    stage_id TEXT,
    status TEXT,
    address1 TEXT,
    address2 TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    category TEXT,
    type TEXT,
    assigned_to_id TEXT,
    assigned_to_name TEXT,
    assigned_to_email TEXT,
    notes TEXT,
    quoted_value REAL DEFAULT 0,
    approved_value REAL DEFAULT 0,
    accounts_receivable REAL DEFAULT 0,
    gross_revenue REAL DEFAULT 0,
    net_revenue REAL DEFAULT 0,
    gross_profit REAL DEFAULT 0,
    gross_margin REAL DEFAULT 0,
    merchant_fees REAL DEFAULT 0,
    refunds REAL DEFAULT 0,
    chargebacks REAL DEFAULT 0,
    contact_id TEXT,
    contact_fname TEXT,
    contact_lname TEXT,
    contact_phone TEXT,
    contact_email TEXT,
    contact_lead_source TEXT,
    custom_field_1 TEXT,
    custom_field_2 TEXT,
    custom_field_3 TEXT,
    custom_field_4 TEXT,
    custom_field_5 TEXT,
    custom_field_6 TEXT,
    custom_field_7 TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_stage ON projects(stage);
CREATE INDEX IF NOT EXISTS idx_projects_assigned ON projects(assigned_to_id);

CREATE TABLE IF NOT EXISTS contacts (
    contact_id TEXT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    phone TEXT,
    email TEXT,
    address1 TEXT,
    address2 TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    assigned_to_id TEXT,
    assigned_to_name TEXT,
    external_id TEXT,
    lead_source TEXT,
    notes TEXT,
    custom_field_1 TEXT,
    custom_field_2 TEXT,
    custom_field_3 TEXT,
    custom_date_1 TEXT,
    custom_date_2 TEXT,
    custom_date_3 TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    project_id TEXT,
    contact_id TEXT,
    type TEXT,
    duration INTEGER,
    start_date TEXT,
    end_date TEXT,
    time_zone TEXT,
    assignee_id TEXT,
    assignee_name TEXT,
    external_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (contact_id) REFERENCES contacts(contact_id)
);

CREATE INDEX IF NOT EXISTS idx_events_project ON events(project_id);
CREATE INDEX IF NOT EXISTS idx_events_start ON events(start_date);

-- ------------------------------------------------------------
-- Webhook-delivered financial data (ProLine API is read-only for these)
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS quotes (
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

CREATE TABLE IF NOT EXISTS invoices (
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

CREATE INDEX IF NOT EXISTS idx_quotes_project ON quotes(project_id);
CREATE INDEX IF NOT EXISTS idx_invoices_project ON invoices(project_id);

CREATE TABLE IF NOT EXISTS webhook_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    webhook_type TEXT,
    project_id TEXT,
    raw_payload TEXT,
    processed INTEGER DEFAULT 0,
    received_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_webhook_log_processed ON webhook_log(processed);

-- ------------------------------------------------------------
-- Agent-derived data (deal quality, notes history, drafts)
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS deal_quality (
    project_id TEXT PRIMARY KEY,
    has_close_date INTEGER DEFAULT 0,
    has_objection INTEGER DEFAULT 0,
    has_deal_amount INTEGER DEFAULT 0,
    has_next_steps INTEGER DEFAULT 0,
    has_followup_date INTEGER DEFAULT 0,
    score INTEGER DEFAULT 0,
    grade TEXT DEFAULT 'F',
    close_date TEXT,
    objection TEXT,
    deal_amount REAL,
    next_steps TEXT,
    followup_date TEXT,
    scored_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE INDEX IF NOT EXISTS idx_deal_quality_grade ON deal_quality(grade);

CREATE TABLE IF NOT EXISTS notes_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    notes_text TEXT,
    notes_hash TEXT,
    source TEXT DEFAULT 'sync',
    captured_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE INDEX IF NOT EXISTS idx_notes_project ON notes_history(project_id);
CREATE INDEX IF NOT EXISTS idx_notes_hash ON notes_history(notes_hash);

CREATE TABLE IF NOT EXISTS draft_emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    contact_email TEXT,
    subject TEXT,
    body TEXT,
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    sent_at DATETIME,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE INDEX IF NOT EXISTS idx_drafts_project ON draft_emails(project_id);
CREATE INDEX IF NOT EXISTS idx_drafts_status ON draft_emails(status);

-- ------------------------------------------------------------
-- Response tracking and marketing attribution
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS response_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT,
    contact_id TEXT,
    inbound_type TEXT,
    inbound_at DATETIME,
    response_at DATETIME,
    response_time_min INTEGER,
    assigned_rep TEXT,
    alerted INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE INDEX IF NOT EXISTS idx_response_waiting ON response_tracking(response_at) WHERE response_at IS NULL;

CREATE TABLE IF NOT EXISTS callrail_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    callrail_id TEXT UNIQUE,
    caller_phone TEXT,
    tracking_number TEXT,
    lead_source TEXT,
    campaign TEXT,
    duration INTEGER,
    recording_url TEXT,
    call_type TEXT,
    matched_contact_id TEXT,
    matched_project_id TEXT,
    call_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (matched_contact_id) REFERENCES contacts(contact_id)
);

CREATE INDEX IF NOT EXISTS idx_callrail_phone ON callrail_calls(caller_phone);
CREATE INDEX IF NOT EXISTS idx_callrail_source ON callrail_calls(lead_source);

-- ------------------------------------------------------------
-- Weather / rain day engine (scripts/weather-check.py)
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS weather_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_type TEXT,
    check_date DATE,
    project_id TEXT,
    job_address TEXT,
    latitude REAL,
    longitude REAL,
    precip_prob_max INTEGER,
    precip_total_mm REAL,
    wind_max_kmh REAL,
    risk_level TEXT,
    decision TEXT,
    trend_vs_evening TEXT,
    raw_hourly_json TEXT,
    checked_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rain_days (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rain_date DATE,
    decision TEXT,
    affected_projects TEXT,
    affected_crews INTEGER,
    estimated_cost REAL,
    notifications_sent INTEGER,
    rescheduled_count INTEGER,
    decided_at DATETIME,
    decided_by TEXT
);

CREATE TABLE IF NOT EXISTS geocode_cache (
    address TEXT PRIMARY KEY,
    latitude REAL,
    longitude REAL,
    display_name TEXT,
    cached_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Operational log
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_type TEXT,
    project_count INTEGER,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    status TEXT
);
