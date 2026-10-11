"""
Munder Difflin — Autonomous Cadence & Eligibility Engine
Determines when divisions should trigger automated production cycles based on
daily post caps, preferred hours, cooldown periods, and system killswitches.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
from core.database import Database
from core.registry import DivisionRegistry
from core.orchestrator import Orchestrator


class CadenceEvaluator:
    """Evaluates whether a division is eligible for an automated production cycle."""

    def __init__(
        self,
        db: Optional[Database] = None,
        registry: Optional[DivisionRegistry] = None,
        orchestrator: Optional[Orchestrator] = None,
        min_cooldown_seconds: int = 120
    ):
        self.db = db or Database()
        self.registry = registry or DivisionRegistry(db=self.db)
        self.orchestrator = orchestrator or Orchestrator(db=self.db)
        self.min_cooldown_seconds = min_cooldown_seconds

    def get_today_production_count(self, division_id: str) -> int:
        """Counts how many jobs were initiated for this division today (UTC)."""
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM jobs WHERE division_id = ? AND date(created_at) = date(?);",
                (division_id, today_str)
            )
            row = cursor.fetchone()
            return row[0] if row else 0

    def get_seconds_since_last_run(self, division_id: str) -> Optional[float]:
        """Returns seconds elapsed since the most recent job for this division."""
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT created_at FROM jobs WHERE division_id = ? ORDER BY created_at DESC LIMIT 1;",
                (division_id,)
            )
            row = cursor.fetchone()
            if not row or not row[0]:
                return None
            try:
                # Parse ISO timestamp
                last_dt = datetime.fromisoformat(row[0])
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                now_utc = datetime.now(timezone.utc)
                return max(0.0, (now_utc - last_dt).total_seconds())
            except Exception:
                return None

    def evaluate_eligibility(self, division_id: str, force: bool = False) -> Tuple[bool, str]:
        """
        Determines if a division should trigger production now.
        Returns: (is_eligible, reason)
        """
        # 1. Killswitch check
        if self.orchestrator.is_emergency_stop_active():
            return False, "Emergency stop killswitch is active"

        # 2. Division existence & enabled check
        division = self.registry.get_division(division_id)
        if not division:
            return False, f"Division '{division_id}' not found in registry"
        if not division.enabled:
            return False, f"Division '{division_id}' is disabled"

        # If forced by operator, bypass caps and cooldowns
        if force:
            return True, "Forced by operator"

        # 3. Daily Cap Check
        max_daily = division.publishing_schedule.max_daily
        produced_today = self.get_today_production_count(division_id)
        if produced_today >= max_daily:
            return False, f"Daily cap reached ({produced_today}/{max_daily} jobs today)"

        # 4. Cooldown Check
        seconds_since = self.get_seconds_since_last_run(division_id)
        if seconds_since is not None and seconds_since < self.min_cooldown_seconds:
            remaining = int(self.min_cooldown_seconds - seconds_since)
            return False, f"Cooldown active ({remaining}s remaining)"

        return True, f"Eligible (Produced {produced_today}/{max_daily} today)"
