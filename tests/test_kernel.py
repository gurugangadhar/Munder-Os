"""
Munder Difflin — Core Kernel Test Suite (Phase 1 Acceptance Tests)
Verifies database integrity, WAL mode, division registry, queue state transitions,
idempotency guarantees, retry logic, and emergency stop killswitch.
"""

import sys
import os
import unittest
import tempfile
import shutil

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Safe stdout reconfigure for Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import truststore
truststore.inject_into_ssl()

from core.database import Database
from core.models import JobStatus
from core.registry import DivisionRegistry
from core.queue import JobQueue
from core.orchestrator import Orchestrator


class TestKernel(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="munder_test_")
        self.db_path = os.path.join(self.test_dir, "test.db")
        self.db = Database(self.db_path)
        self.queue = JobQueue(self.db)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_database_and_wal_mode(self):
        """Verify database initializes properly and WAL mode is active."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode;")
        mode = cursor.fetchone()[0]
        conn.close()
        self.assertEqual(mode.lower(), "wal")

    def test_division_registry_sync(self):
        """Verify registry loads YAML and syncs to SQLite."""
        registry = DivisionRegistry(db=self.db)
        divs = registry.get_all_divisions()
        self.assertGreaterEqual(len(divs), 7)
        
        div_a = registry.get_division("div_a_tech")
        self.assertIsNotNone(div_a)
        self.assertEqual(div_a.name, "AI & Technology Media")
        self.assertTrue(div_a.enabled)

    def test_queue_enqueue_and_idempotency(self):
        """Verify jobs can be enqueued and identical jobs return the same record."""
        # Sync divisions first
        DivisionRegistry(db=self.db)

        job1 = self.queue.enqueue("div_a_tech", "Building Autonomous Agents with Python")
        self.assertIsNotNone(job1.job_id)
        self.assertEqual(job1.status, JobStatus.QUEUED)

        # Enqueue same topic on same day -> must return existing job
        job2 = self.queue.enqueue("div_a_tech", "Building Autonomous Agents with Python")
        self.assertEqual(job1.job_id, job2.job_id)
        self.assertEqual(job1.idempotency_key, job2.idempotency_key)

    def test_queue_dequeue_and_priority(self):
        """Verify dequeue respects division priority and transitions status to PROCESSING."""
        DivisionRegistry(db=self.db)

        # div_e has priority 5, div_a has priority 1
        job_e = self.queue.enqueue("div_e_pinterest", "Cheatsheet Topic")
        job_a = self.queue.enqueue("div_a_tech", "High Priority AI Topic")

        dequeued = self.queue.dequeue()
        self.assertIsNotNone(dequeued)
        # div_a has priority 1, so it must be dequeued before div_e
        self.assertEqual(dequeued.division_id, "div_a_tech")
        self.assertEqual(dequeued.job_id, job_a.job_id)
        self.assertEqual(dequeued.status, JobStatus.PROCESSING)

    def test_retry_mechanism(self):
        """Verify retry counter increments and transitions to FAILED on max retries."""
        DivisionRegistry(db=self.db)

        job = self.queue.enqueue("div_a_tech", "Failing Job Topic", max_retries=2)
        
        # Retry 1
        retried1 = self.queue.retry_job(job.job_id, error_message="Network glitch 1")
        self.assertEqual(retried1.retry_count, 1)
        self.assertEqual(retried1.status, JobStatus.QUEUED)

        # Retry 2 (max_retries reached)
        retried2 = self.queue.retry_job(job.job_id, error_message="Network glitch 2")
        self.assertEqual(retried2.retry_count, 2)
        self.assertEqual(retried2.status, JobStatus.FAILED)

    def test_approval_flow(self):
        """Verify operator approval transition."""
        DivisionRegistry(db=self.db)

        job = self.queue.enqueue("div_a_tech", "Pending Review Topic")
        self.queue.update_status(job.job_id, JobStatus.AWAITING_APPROVAL)

        approved = self.queue.approve_job(job.job_id)
        self.assertEqual(approved.status, JobStatus.READY_FOR_PUBLISH)

    def test_emergency_stop(self):
        """Verify orchestrator respects emergency stop killswitch."""
        registry = DivisionRegistry(db=self.db)
        orch = Orchestrator(db=self.db, queue=self.queue, registry=registry)
        
        # Initially disengaged
        orch.set_emergency_stop(False)
        self.assertFalse(orch.is_emergency_stop_active())

        # Engage emergency stop
        orch.set_emergency_stop(True)
        self.assertTrue(orch.is_emergency_stop_active())

        # Worker should refuse execution
        job = self.queue.enqueue("div_a_tech", "Test Topic Under Pause")
        processed = orch.run_next_job(lambda j: {"ok": True})
        self.assertIsNone(processed)

        # Disengage
        orch.set_emergency_stop(False)
        self.assertFalse(orch.is_emergency_stop_active())


if __name__ == "__main__":
    unittest.main()
