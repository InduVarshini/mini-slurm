"""Database functions for mini-slurm."""

import os
import sqlite3
from pathlib import Path

DB_PATH = os.path.expanduser("~/.mini_slurm.db")


def init_db(db_path: str = DB_PATH):
    """Initialize the SQLite database with the jobs table."""
    Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            command TEXT NOT NULL,
            cpus INTEGER NOT NULL,
            mem_mb INTEGER NOT NULL,
            status TEXT NOT NULL,
            priority INTEGER NOT NULL DEFAULT 0,
            submit_time REAL NOT NULL,
            start_time REAL,
            end_time REAL,
            wait_time REAL,
            runtime REAL,
            return_code INTEGER,
            user TEXT,
            stdout_path TEXT,
            stderr_path TEXT,
            cpu_user_time REAL,
            cpu_system_time REAL,
            is_elastic INTEGER NOT NULL DEFAULT 0,
            min_cpus INTEGER,
            max_cpus INTEGER,
            current_cpus INTEGER,
            control_file TEXT
        )
        """
    )
    # Add elastic columns to existing databases (migration)
    try:
        c.execute("ALTER TABLE jobs ADD COLUMN is_elastic INTEGER NOT NULL DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Column already exists
    try:
        c.execute("ALTER TABLE jobs ADD COLUMN min_cpus INTEGER")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE jobs ADD COLUMN max_cpus INTEGER")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE jobs ADD COLUMN current_cpus INTEGER")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE jobs ADD COLUMN control_file TEXT")
    except sqlite3.OperationalError:
        pass
    # Add topology columns
    try:
        c.execute("ALTER TABLE jobs ADD COLUMN nodes TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()


def get_conn():
    """Get a database connection."""
    return sqlite3.connect(DB_PATH)
