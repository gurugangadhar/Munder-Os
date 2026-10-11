"""
Munder Difflin — Persistent FIFO Job Queue
Atomic, resilient state machine backed by SQLite WAL mode.
"""

import uuid
import hashlib
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from core.models import Job, JobStatus
from core.database import Database


class JobQueue:
    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()

    def generate_idempotency_key(self, division_id: str, topic: str, date_str: Optional[str] = None) -> str:
        """Generates deterministic hash to prevent duplicate publishing."""
        date_part = date_str or datetime.now().strftime("%Y-%m-%d")
        normalized = f"{division_id}:{topic.strip().lower()}:{date_part}"
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

    def enqueue(
        self,
        division_id: str,
        topic: str,
        payload: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        max_retries: int = 3
    ) -> Job:
        """Enqueues a new job or returns existing active job with same idempotency key."""
        payload = payload or {}
        key = idempotency_key or self.generate_idempotency_key(division_id, topic)
        now = datetime.now().isoformat()

        with self.db.transaction() as conn:
            cursor = conn.cursor()
            
            # Check for existing job with same idempotency key
            cursor.execute("SELECT * FROM jobs WHERE idempotency_key = ?", (key,))
            existing = cursor.fetchone()
            if existing:
                row_dict = dict(existing)
                row_dict["payload"] = json.loads(row_dict["payload_json"])
                del row_dict["payload_json"]
                return Job(**row_dict)

            # Insert new job
            job_id = f"job_{uuid.uuid4().hex[:12]}"
            cursor.execute("""
            INSERT INTO jobs (
                job_id, division_id, idempotency_key, status, topic,
                stage, retry_count, max_retries, payload_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                job_id,
                division_id,
                key,
                JobStatus.QUEUED.value,
                topic,
                "init",
                0,
                max_retries,
                json.dumps(payload),
                now,
                now
            ))

        return self.get_job(job_id)

    def dequeue(self) -> Optional[Job]:
        """
        Atomically fetches the next available QUEUED job.
        Prioritizes by division priority, then job creation timestamp.
        """
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT j.* FROM jobs j
            JOIN divisions d ON j.division_id = d.id
            WHERE j.status = ? AND d.enabled = 1
            ORDER BY d.priority ASC, j.created_at ASC
            LIMIT 1;
            """, (JobStatus.QUEUED.value,))
            row = cursor.fetchone()
            if not row:
                return None

            job_id = row["job_id"]
            now = datetime.now().isoformat()
            cursor.execute("""
            UPDATE jobs
            SET status = ?, stage = 'started', updated_at = ?
            WHERE job_id = ?;
            """, (JobStatus.PROCESSING.value, now, job_id))

        return self.get_job(job_id)

    def update_status(
        self,
        job_id: str,
        status: JobStatus,
        stage: Optional[str] = None,
        error_message: Optional[str] = None,
        payload_updates: Optional[Dict[str, Any]] = None
    ) -> Optional[Job]:
        """Updates the status and optional payload of an active job."""
        now = datetime.now().isoformat()
        job = self.get_job(job_id)
        if not job:
            return None

        merged_payload = dict(job.payload)
        if payload_updates:
            merged_payload.update(payload_updates)

        completed_at = now if status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED) else job.completed_at

        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE jobs
            SET status = ?,
                stage = COALESCE(?, stage),
                error_message = ?,
                payload_json = ?,
                updated_at = ?,
                completed_at = ?
            WHERE job_id = ?;
            """, (
                status.value,
                stage,
                error_message,
                json.dumps(merged_payload),
                now,
                completed_at.isoformat() if isinstance(completed_at, datetime) else completed_at,
                job_id
            ))

        return self.get_job(job_id)

    def retry_job(self, job_id: str, error_message: str) -> Optional[Job]:
        """Increments retry counter; re-queues if within limit, else marks FAILED."""
        job = self.get_job(job_id)
        if not job:
            return None

        new_retries = job.retry_count + 1
        now = datetime.now().isoformat()

        if new_retries < job.max_retries:
            next_status = JobStatus.QUEUED
            next_stage = f"retry_{new_retries}"
        else:
            next_status = JobStatus.FAILED
            next_stage = "retries_exhausted"

        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE jobs
            SET status = ?,
                stage = ?,
                retry_count = ?,
                error_message = ?,
                updated_at = ?
            WHERE job_id = ?;
            """, (
                next_status.value,
                next_stage,
                new_retries,
                error_message,
                now,
                job_id
            ))

        return self.get_job(job_id)

    def approve_job(self, job_id: str) -> Optional[Job]:
        """Transitions job from AWAITING_APPROVAL to READY_FOR_PUBLISH."""
        job = self.get_job(job_id)
        if not job or job.status != JobStatus.AWAITING_APPROVAL:
            return None
        return self.update_status(job_id, JobStatus.READY_FOR_PUBLISH, stage="approved_by_operator")

    def get_job(self, job_id: str) -> Optional[Job]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if not row:
                return None
            row_dict = dict(row)
            row_dict["payload"] = json.loads(row_dict["payload_json"])
            del row_dict["payload_json"]
            return Job(**row_dict)
        finally:
            conn.close()

    def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        division_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Job]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM jobs WHERE 1=1"
            params: List[Any] = []
            if status:
                query += " AND status = ?"
                params.append(status.value)
            if division_id:
                query += " AND division_id = ?"
                params.append(division_id)
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            results = []
            for r in rows:
                row_dict = dict(r)
                row_dict["payload"] = json.loads(row_dict["payload_json"])
                del row_dict["payload_json"]
                results.append(Job(**row_dict))
            return results
        finally:
            conn.close()

    def get_queue_stats(self) -> Dict[str, int]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT status, COUNT(*) as cnt FROM jobs GROUP BY status;")
            rows = cursor.fetchall()
            stats = {s.value: 0 for s in JobStatus}
            for r in rows:
                stats[r["status"]] = r["cnt"]
            return stats
        finally:
            conn.close()
