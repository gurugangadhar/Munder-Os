"""
Munder Difflin — Business Division Registry
Loads, validates, and manages division configurations.
"""

import os
import yaml
import json
from datetime import datetime
from typing import List, Dict, Optional
from core.models import DivisionConfig
from core.database import Database

DEFAULT_DIVISIONS_FILE = "config/divisions.yaml"


class DivisionRegistry:
    def __init__(self, config_path: str = DEFAULT_DIVISIONS_FILE, db: Optional[Database] = None):
        self.config_path = config_path
        self.db = db or Database()
        self._divisions: Dict[str, DivisionConfig] = {}
        self.reload()

    def reload(self):
        """Loads YAML, parses into Pydantic models, and syncs to SQLite."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Divisions config file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        parsed_divisions = {}
        for item in raw.get("divisions", []):
            div = DivisionConfig(**item)
            parsed_divisions[div.id] = div

        self._divisions = parsed_divisions
        self._sync_to_database()

    def _sync_to_database(self):
        """Persists division definitions into the SQLite database."""
        now = datetime.now().isoformat()
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            for div in self._divisions.values():
                cursor.execute("""
                INSERT INTO divisions (id, name, enabled, priority, config_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    enabled = excluded.enabled,
                    priority = excluded.priority,
                    config_json = excluded.config_json,
                    updated_at = excluded.updated_at;
                """, (
                    div.id,
                    div.name,
                    1 if div.enabled else 0,
                    div.priority,
                    div.model_dump_json(),
                    now
                ))

    def get_division(self, division_id: str) -> Optional[DivisionConfig]:
        return self._divisions.get(division_id)

    def get_all_divisions(self) -> List[DivisionConfig]:
        return sorted(list(self._divisions.values()), key=lambda d: d.priority)

    def get_active_divisions(self) -> List[DivisionConfig]:
        return [d for d in self.get_all_divisions() if d.enabled]
