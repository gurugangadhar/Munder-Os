"""
Munder Difflin — SQLite Database Core
Local-first, high-resilience database engine using SQLite with WAL mode.
"""

import sqlite3
import os
import json
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

DEFAULT_DB_PATH = "data/munder_difflin.db"


class Database:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self.initialize_schema()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        # Enable WAL (Write-Ahead Logging) for safe concurrent reads & writes
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    @contextmanager
    def transaction(self):
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize_schema(self):
        """Creates all required tables and indexes if they do not exist."""
        with self.transaction() as conn:
            cursor = conn.cursor()
            
            # 1. Divisions Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS divisions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                priority INTEGER NOT NULL DEFAULT 1,
                config_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)

            # 2. Jobs Table (Queue State Machine)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                division_id TEXT NOT NULL,
                idempotency_key TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL,
                topic TEXT NOT NULL,
                stage TEXT NOT NULL DEFAULT 'init',
                retry_count INTEGER NOT NULL DEFAULT 0,
                max_retries INTEGER NOT NULL DEFAULT 3,
                payload_json TEXT NOT NULL,
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (division_id) REFERENCES divisions(id) ON DELETE CASCADE
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_division ON jobs(division_id);")

            # 3. Research Topic Candidates Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                candidate_id TEXT PRIMARY KEY,
                division_id TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                source_url TEXT NOT NULL,
                credibility_score REAL NOT NULL DEFAULT 1.0,
                discovered_at TEXT NOT NULL,
                used_in_job_id TEXT,
                FOREIGN KEY (division_id) REFERENCES divisions(id) ON DELETE CASCADE
            );
            """)

            # 4. Scripts Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS scripts (
                job_id TEXT PRIMARY KEY,
                division_id TEXT NOT NULL,
                title TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
            );
            """)

            # 5. Rendered Assets Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                job_id TEXT PRIMARY KEY,
                division_id TEXT NOT NULL,
                video_path TEXT,
                audio_path TEXT,
                subtitles_path TEXT,
                thumbnail_path TEXT,
                qa_passed INTEGER NOT NULL DEFAULT 0,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
            );
            """)

            # 6. Official Publications Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS publications (
                publication_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                division_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                platform_item_id TEXT NOT NULL,
                canonical_url TEXT NOT NULL,
                published_at TEXT NOT NULL,
                privacy_status TEXT NOT NULL DEFAULT 'public',
                FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pub_platform ON publications(platform);")

            # 7. Analytics History Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                publication_id TEXT NOT NULL,
                views INTEGER NOT NULL DEFAULT 0,
                likes INTEGER NOT NULL DEFAULT 0,
                shares INTEGER NOT NULL DEFAULT 0,
                comments INTEGER NOT NULL DEFAULT 0,
                watch_time_hours REAL NOT NULL DEFAULT 0.0,
                recorded_at TEXT NOT NULL,
                FOREIGN KEY (publication_id) REFERENCES publications(publication_id) ON DELETE CASCADE
            );
            """)

            # 8. Financial Ledger Table (Strict ₹0 Tracking)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_ledger (
                entry_id TEXT PRIMARY KEY,
                division_id TEXT NOT NULL,
                type TEXT NOT NULL, -- 'REVENUE' or 'EXPENSE'
                amount_inr REAL NOT NULL DEFAULT 0.0,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                job_id TEXT,
                timestamp TEXT NOT NULL
            );
            """)

            # 9. System Health & Heartbeat Logs Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT NOT NULL,
                disk_free_gb REAL NOT NULL,
                active_jobs INTEGER NOT NULL DEFAULT 0,
                issues_json TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );
            """)
