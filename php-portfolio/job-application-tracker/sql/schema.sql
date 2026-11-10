-- Job Application Tracker schema (SQLite). Safe to run repeatedly.

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name          TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS applications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company     TEXT NOT NULL,
    role        TEXT NOT NULL,
    url         TEXT NOT NULL DEFAULT '',
    location    TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'applied'
                CHECK (status IN ('wishlist','applied','screening','interview','offer','accepted','rejected','withdrawn')),
    applied_on  TEXT,                       -- YYYY-MM-DD, NULL while still on the wishlist
    salary_note TEXT NOT NULL DEFAULT '',
    notes       TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_app_user_status ON applications(user_id, status);
CREATE INDEX IF NOT EXISTS idx_app_user_applied ON applications(user_id, applied_on);

-- Every status change is logged so we can compute response rate and time spent per stage.
CREATE TABLE IF NOT EXISTS status_events (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    status         TEXT NOT NULL,
    changed_on     TEXT NOT NULL,           -- YYYY-MM-DD
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_events_app ON status_events(application_id, changed_on);

CREATE TABLE IF NOT EXISTS reminders (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    due_on         TEXT NOT NULL,           -- YYYY-MM-DD
    note           TEXT NOT NULL,
    done           INTEGER NOT NULL DEFAULT 0,
    sent_at        TEXT                     -- set by bin/send_reminders.php
);
CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(done, due_on);

CREATE TABLE IF NOT EXISTS login_attempts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    email        TEXT NOT NULL COLLATE NOCASE,
    ip           TEXT NOT NULL,
    attempted_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_login_email ON login_attempts(email, attempted_at);
