"""
Munder Difflin — Executive Business Manager (Orchestrator)
Orchestrates job dispatch, enforces limits, quiet hours, health checks, and emergency stops.
"""

import os
import shutil
import yaml
from typing import Optional, Tuple, Callable, Any, Dict, List
from core.models import Job, JobStatus, SystemHealthReport
from core.database import Database
from core.queue import JobQueue
from core.registry import DivisionRegistry

SYSTEM_CONFIG_FILE = "config/system.yaml"
EMERGENCY_STOP_FILE = "config/emergency_stop.flag"


class Orchestrator:
    def __init__(
        self,
        db: Optional[Database] = None,
        queue: Optional[JobQueue] = None,
        registry: Optional[DivisionRegistry] = None,
        system_config_path: str = SYSTEM_CONFIG_FILE
    ):
        self.db = db or Database()
        self.queue = queue or JobQueue(self.db)
        self.registry = registry or DivisionRegistry(db=self.db)
        self.system_config_path = system_config_path
        self._load_system_config()

    def _load_system_config(self):
        if os.path.exists(self.system_config_path):
            with open(self.system_config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {
                "system": {"supervised_mode": True, "emergency_stop_flag": EMERGENCY_STOP_FILE},
                "execution": {"min_disk_free_gb": 5.0, "daily_global_job_cap": 20, "quiet_hours": {"enabled": False}}
            }

    def is_emergency_stop_active(self) -> bool:
        """Returns True if the physical killswitch file exists or env var is set."""
        flag_path = self.config.get("system", {}).get("emergency_stop_flag", EMERGENCY_STOP_FILE)
        if os.path.exists(flag_path):
            return True
        return os.environ.get("EMERGENCY_STOP", "false").lower() in ("true", "1", "yes")

    def set_emergency_stop(self, active: bool):
        """Creates or removes the physical emergency stop flag file."""
        flag_path = self.config.get("system", {}).get("emergency_stop_flag", EMERGENCY_STOP_FILE)
        os.makedirs(os.path.dirname(os.path.abspath(flag_path)), exist_ok=True)
        if active:
            with open(flag_path, "w", encoding="utf-8") as f:
                f.write(f"EMERGENCY_STOP_TRIGGERED_AT={datetime.now().isoformat()}\n")
        else:
            if os.path.exists(flag_path):
                os.remove(flag_path)

    def check_system_health(self) -> SystemHealthReport:
        """Inspects disk space, active jobs, and emergency status."""
        issues = []
        status = "HEALTHY"

        # Check disk space
        min_disk = self.config.get("execution", {}).get("min_disk_free_gb", 5.0)
        try:
            _, _, free = shutil.disk_usage("C:\\")
            free_gb = round(free / (1024**3), 1)
        except Exception:
            free_gb = 50.0

        if free_gb < min_disk:
            status = "CRITICAL"
            issues.append(f"Low disk space: {free_gb} GB remaining (threshold: {min_disk} GB)")

        # Check emergency stop
        stop_active = self.is_emergency_stop_active()
        if stop_active:
            status = "PAUSED"
            issues.append("Emergency stop is currently engaged.")

        # Check queue stats
        stats = self.queue.get_queue_stats()
        active_jobs = stats.get(JobStatus.PROCESSING.value, 0)
        pending_approvals = stats.get(JobStatus.AWAITING_APPROVAL.value, 0)
        failed_jobs = stats.get(JobStatus.FAILED.value, 0)

        report = SystemHealthReport(
            status=status,
            disk_free_gb=free_gb,
            active_jobs_count=active_jobs,
            pending_approvals_count=pending_approvals,
            failed_jobs_count=failed_jobs,
            emergency_stop_active=stop_active,
            issues=issues
        )

        # Log heartbeat to DB
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            import json
            cursor.execute("""
            INSERT INTO system_health (status, disk_free_gb, active_jobs, issues_json, timestamp)
            VALUES (?, ?, ?, ?, ?);
            """, (status, free_gb, active_jobs, json.dumps(issues), datetime.now().isoformat()))

        return report

    def is_in_quiet_hours(self) -> bool:
        qh = self.config.get("execution", {}).get("quiet_hours", {})
        if not qh.get("enabled", False):
            return False
        now_time = datetime.now().strftime("%H:%M")
        start = qh.get("start", "23:00")
        end = qh.get("end", "07:00")
        if start > end:  # Spans midnight
            return now_time >= start or now_time <= end
        return start <= now_time <= end

    def can_execute_now(self, division_id: str) -> Tuple[bool, str]:
        """Validates all gate conditions before initiating a production run."""
        if self.is_emergency_stop_active():
            return False, "Emergency stop is active."

        health = self.check_system_health()
        if health.status == "CRITICAL":
            return False, f"System health is CRITICAL: {', '.join(health.issues)}"

        if self.is_in_quiet_hours():
            return False, "Currently in quiet hours."

        div = self.registry.get_division(division_id)
        if not div:
            return False, f"Division '{division_id}' not found in registry."
        if not div.enabled:
            return False, f"Division '{division_id}' is currently disabled."

        # Check daily division cap
        today_prefix = datetime.now().strftime("%Y-%m-%d")
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE division_id = ? AND status = ? AND created_at LIKE ?;
            """, (division_id, JobStatus.COMPLETED.value, f"{today_prefix}%"))
            completed_today = cursor.fetchone()[0]
            if completed_today >= div.publishing_schedule.max_daily:
                return False, f"Division daily production cap reached ({completed_today}/{div.publishing_schedule.max_daily})."
        finally:
            conn.close()

        return True, "Ready"

    def run_next_job(self, worker_fn: Callable[[Job], Any]) -> Optional[Job]:
        """
        Pulls the next queued job and executes it through the provided worker function.
        Handles errors, auto-retries, and state transitions.
        """
        # Global checks
        if self.is_emergency_stop_active():
            return None

        job = self.queue.dequeue()
        if not job:
            return None

        can_run, reason = self.can_execute_now(job.division_id)
        if not can_run:
            self.queue.update_status(job.job_id, JobStatus.QUEUED, stage="deferred", error_message=reason)
            return None

        try:
            # Execute worker logic
            result = worker_fn(job)
            supervised = self.config.get("system", {}).get("supervised_mode", True)
            
            # If supervised mode is on, transition to AWAITING_APPROVAL
            # Otherwise mark READY_FOR_PUBLISH or COMPLETED based on result
            if supervised and job.status != JobStatus.READY_FOR_PUBLISH:
                next_status = JobStatus.AWAITING_APPROVAL
                stage = "awaiting_operator_review"
            else:
                next_status = JobStatus.COMPLETED
                stage = "done"

            payload_updates = {"worker_result": result} if result else None
            return self.queue.update_status(job.job_id, next_status, stage=stage, payload_updates=payload_updates)

        except Exception as e:
            return self.queue.retry_job(job.job_id, error_message=str(e))
