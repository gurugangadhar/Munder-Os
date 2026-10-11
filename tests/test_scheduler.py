"""
Unit Test Suite for Autonomous Scheduler & Cadence Engine (Phase 4)
Tests eligibility evaluation, daily cap constraints, cooldown enforcement,
killswitch compliance, and autonomous cycle execution.
"""

import os
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from core.database import Database
from core.registry import DivisionRegistry
from core.orchestrator import Orchestrator
from core.queue import JobQueue
from core.scheduler import AutonomousScheduler, CadenceEvaluator
from core.publishing.manager import PublishingManager

TEST_DB_PATH = "data/test_scheduler.db"


class TestSchedulerPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        cls.db = Database(TEST_DB_PATH)
        cls.registry = DivisionRegistry(db=cls.db)
        cls.orchestrator = Orchestrator(db=cls.db)
        cls.queue = JobQueue(db=cls.db)
        cls.publishing_mgr = PublishingManager(db=cls.db)

        # DivisionRegistry automatically syncs config/divisions.yaml to test db on init
        pass

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass

    def setUp(self):
        # Reset jobs table for test isolation
        with self.db.transaction() as conn:
            conn.cursor().execute("DELETE FROM publications;")
            conn.cursor().execute("DELETE FROM jobs;")

    def test_01_cadence_eligibility(self):
        """Verify division eligibility starts True and flips to False when cap is reached."""
        evaluator = CadenceEvaluator(db=self.db, registry=self.registry, orchestrator=self.orchestrator, min_cooldown_seconds=10)
        
        eligible, reason = evaluator.evaluate_eligibility("div_a_tech")
        self.assertTrue(eligible, f"Expected division to be eligible, got: {reason}")

        # Simulate reaching max_daily cap (max_daily for div_a_tech is 2)
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            for i in range(2):
                cursor.execute("""
                INSERT INTO jobs (job_id, division_id, idempotency_key, status, topic, stage, retry_count, max_retries, payload_json, created_at, updated_at)
                VALUES (?, 'div_a_tech', ?, 'COMPLETED', 'Test', 'qa', 0, 3, '{}', ?, ?);
                """, (f"job_cap_{i}", f"key_cap_{i}", now_iso, now_iso))

        eligible, reason = evaluator.evaluate_eligibility("div_a_tech")
        self.assertFalse(eligible, "Expected division to be ineligible due to daily cap")
        self.assertIn("Daily cap reached", reason)

    def test_02_cooldown_enforcement(self):
        """Verify cooldown period prevents back-to-back automated execution."""
        evaluator = CadenceEvaluator(db=self.db, registry=self.registry, orchestrator=self.orchestrator, min_cooldown_seconds=300)

        # Insert 1 job that completed 10 seconds ago
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.db.transaction() as conn:
            conn.cursor().execute("""
            INSERT INTO jobs (job_id, division_id, idempotency_key, status, topic, stage, retry_count, max_retries, payload_json, created_at, updated_at)
            VALUES ('job_cooldown', 'div_a_tech', 'key_cool', 'COMPLETED', 'Test', 'qa', 0, 3, '{}', ?, ?);
            """, (now_iso, now_iso))

        eligible, reason = evaluator.evaluate_eligibility("div_a_tech")
        self.assertFalse(eligible)
        self.assertIn("Cooldown active", reason)

        # Force bypasses cooldown
        forced_eligible, _ = evaluator.evaluate_eligibility("div_a_tech", force=True)
        self.assertTrue(forced_eligible)

    def test_03_emergency_stop_killswitch(self):
        """Verify emergency stop halts all scheduling immediately."""
        evaluator = CadenceEvaluator(db=self.db, registry=self.registry, orchestrator=self.orchestrator)
        
        # Activate killswitch via orchestrator
        self.orchestrator.set_emergency_stop(True)

        eligible, reason = evaluator.evaluate_eligibility("div_a_tech")
        self.assertFalse(eligible)
        self.assertIn("Emergency stop", reason)

        # Reset killswitch
        self.orchestrator.set_emergency_stop(False)
        eligible, _ = evaluator.evaluate_eligibility("div_a_tech")
        self.assertTrue(eligible)

    def test_04_scheduler_telemetry_status(self):
        """Verify get_status returns accurate telemetry and division metrics."""
        scheduler = AutonomousScheduler(
            db=self.db,
            registry=self.registry,
            orchestrator=self.orchestrator,
            publishing_mgr=self.publishing_mgr
        )

        status = scheduler.get_status()
        self.assertIn("is_running", status)
        self.assertIn("divisions", status)
        self.assertFalse(status["is_running"])
        self.assertGreater(len(status["divisions"]), 0)

        div_a = next(d for d in status["divisions"] if d["id"] == "div_a_tech")
        self.assertEqual(div_a["daily_cap"], 2)

    def test_05_autonomous_cycle_execution(self):
        """Verify run_division_cycle creates a job and records publication."""
        scheduler = AutonomousScheduler(
            db=self.db,
            registry=self.registry,
            orchestrator=self.orchestrator,
            publishing_mgr=self.publishing_mgr
        )

        # Mock the heavy video rendering step so test runs in <1 second
        mock_manifest = {
            "title": "Mock Autonomous Video",
            "video_path": "data/test_short.mp4",
            "youtube_metadata": {"description": "Mock description", "tags": ["AI", "Shorts"]}
        }

        # Create dummy file if not exists
        os.makedirs("data", exist_ok=True)
        with open("data/test_short.mp4", "wb") as f:
            f.write(b"\x00" * 1024)

        with patch.object(scheduler.pipeline, "run_division_a_production", return_value={"success": True, "manifest": mock_manifest}):
            result = scheduler.run_division_cycle("div_a_tech", force=True)
            self.assertTrue(result["success"])
            self.assertIn("publication", result)
            self.assertTrue(result["publication"]["success"])

            # Verify recorded in DB
            with self.db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM jobs WHERE division_id = 'div_a_tech';")
                self.assertEqual(cursor.fetchone()[0], 1)
                cursor.execute("SELECT COUNT(*) FROM publications WHERE division_id = 'div_a_tech';")
                self.assertEqual(cursor.fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
