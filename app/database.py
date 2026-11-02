import sqlite3
from pathlib import Path
from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS triage_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    customer_impact TEXT NOT NULL,
    frequency TEXT NOT NULL,
    platform TEXT NOT NULL,
    source TEXT NOT NULL,
    priority TEXT NOT NULL,
    category TEXT NOT NULL,
    owner_team TEXT NOT NULL,
    impact_level TEXT NOT NULL,
    confidence INTEGER NOT NULL,
    summary TEXT NOT NULL,
    rationale TEXT NOT NULL,
    next_action TEXT NOT NULL,
    labels_json TEXT NOT NULL,
    acceptance_criteria_json TEXT NOT NULL,
    follow_up_questions_json TEXT NOT NULL,
    mode TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_triage_created_at ON triage_runs(created_at);
CREATE INDEX IF NOT EXISTS idx_triage_priority ON triage_runs(priority);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    db_path = Path(app.config["DATABASE"])
    if not db_path.is_absolute():
        db_path = Path(app.root_path).parent / db_path
        app.config["DATABASE"] = str(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(app.config["DATABASE"]) as db:
        db.executescript(SCHEMA)
        db.commit()
    app.teardown_appcontext(close_db)
