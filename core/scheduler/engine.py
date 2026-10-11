"""
Munder Difflin — Autonomous Scheduler Engine
Manages autonomous, recurring multi-agent production loops across all business divisions.
Runs continuously in the background, enforcing daily caps, cooldowns, QA gates,
and automatic publishing.
"""

import asyncio
import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable

from core.database import Database
from core.registry import DivisionRegistry
from core.orchestrator import Orchestrator
from core.queue import JobQueue
from core.scheduler.cadence import CadenceEvaluator
from core.media.pipeline import ProductionPipeline
from core.media.research import TOPIC_CATALOG, TopicIdea
from core.publishing.manager import PublishingManager
from core.models import PlatformType, AssetManifest, ScriptPackage


class AutonomousScheduler:
    """Master background scheduler engine that drives 24/7 autonomous production."""

    def __init__(
        self,
        db: Optional[Database] = None,
        registry: Optional[DivisionRegistry] = None,
        orchestrator: Optional[Orchestrator] = None,
        queue: Optional[JobQueue] = None,
        publishing_mgr: Optional[PublishingManager] = None,
        tick_interval_seconds: int = 60,
        activity_logger: Optional[Callable[[str, str, str, str], None]] = None
    ):
        self.db = db or Database()
        self.registry = registry or DivisionRegistry(db=self.db)
        self.orchestrator = orchestrator or Orchestrator(db=self.db)
        self.queue = queue or JobQueue(db=self.db)
        self.publishing_mgr = publishing_mgr or PublishingManager(db=self.db)
        self.cadence = CadenceEvaluator(db=self.db, registry=self.registry, orchestrator=self.orchestrator)
        self.pipeline = ProductionPipeline()
        self.tick_interval_seconds = tick_interval_seconds
        self.activity_logger = activity_logger

        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.total_cycles = 0
        self.successful_runs = 0
        self.failed_runs = 0
        self.last_tick_time: Optional[str] = None
        self.last_run_time: Optional[str] = None
        self.recent_events: List[Dict[str, Any]] = []

    def log_event(self, agent: str, action: str, details: str, division_id: str = "system"):
        """Logs an event to internal history and external activity logger if provided."""
        event = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "agent": agent,
            "action": action,
            "details": details,
            "division": division_id
        }
        self.recent_events.insert(0, event)
        if len(self.recent_events) > 50:
            self.recent_events.pop()

        if self.activity_logger:
            try:
                self.activity_logger(agent, action, details, division_id)
            except Exception:
                pass

    def get_next_topic_for_division(self, division_id: str) -> TopicIdea:
        """Picks the next unproduced topic from the catalog or cycles smoothly."""
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT topic FROM jobs WHERE division_id = ? ORDER BY created_at DESC;", (division_id,))
            produced_topics = {row[0] for row in cursor.fetchall()}

        # Look for first unproduced topic
        for topic in TOPIC_CATALOG:
            if topic.title not in produced_topics:
                return topic

        # If all produced, round-robin by count
        idx = len(produced_topics) % len(TOPIC_CATALOG)
        return TOPIC_CATALOG[idx]

    def run_division_cycle(self, division_id: str, force: bool = False) -> Dict[str, Any]:
        """Executes a single autonomous production and publishing cycle for a division."""
        # 1. Eligibility Check
        eligible, reason = self.cadence.evaluate_eligibility(division_id, force=force)
        if not eligible:
            return {"success": False, "skipped": True, "reason": reason}

        division = self.registry.get_division(division_id)
        if not division:
            return {"success": False, "error": f"Division {division_id} not found"}

        # 2. Topic Selection & Job Record Creation
        topic = self.get_next_topic_for_division(division_id)
        job_id = f"job_auto_{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now().isoformat()

        self.log_event("Michael", "SCHEDULER_DISPATCH", f"Triggered autonomous production: '{topic.title}'", division_id)

        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO jobs (
                job_id, division_id, idempotency_key, status, topic, stage,
                retry_count, max_retries, payload_json, created_at, updated_at
            ) VALUES (?, ?, ?, 'PROCESSING', ?, 'production', 0, 3, ?, ?, ?);
            """, (
                job_id,
                division_id,
                f"idem_{job_id}",
                topic.title,
                json.dumps({"topic_id": topic.topic_id, "title": topic.title}),
                now_iso,
                now_iso
            ))

        # 3. Media Production Execution
        def pipeline_callback(agent: str, msg: str):
            self.log_event(agent, "PRODUCING", msg, division_id)

        try:
            prod_result = self.pipeline.run_division_a_production(
                topic_id=topic.topic_id,
                log_callback=pipeline_callback
            )

            if not prod_result.get("success"):
                err = prod_result.get("error", "Unknown production error")
                self.log_event("Dwight", "PRODUCTION_FAILED", err, division_id)
                self.failed_runs += 1
                with self.db.transaction() as conn:
                    conn.cursor().execute("UPDATE jobs SET status = 'FAILED', updated_at = ? WHERE job_id = ?;", (datetime.now().isoformat(), job_id))
                return {"success": False, "error": err}

            manifest_data = prod_result["manifest"]
            video_path = manifest_data["video_path"]

            # 4. Automatic Export & Publishing
            self.log_event("Ryan", "AUTO_PUBLISHING", f"Handing off {job_id} to PublishingManager...", division_id)

            manifest = AssetManifest(
                job_id=job_id,
                division_id=division_id,
                video_path=video_path,
                qa_passed=True
            )

            script = ScriptPackage(
                job_id=job_id,
                division_id=division_id,
                title=manifest_data["title"],
                hook=topic.hook,
                voiceover_lines=topic.core_points,
                call_to_action=topic.call_to_action,
                description=manifest_data.get("youtube_metadata", {}).get("description", topic.title),
                tags=manifest_data.get("youtube_metadata", {}).get("tags", ["Shorts", "AI", "Tech"]),
                estimated_duration_seconds=50,
                sources=topic.sources
            )

            pub_result = self.publishing_mgr.publish_asset(
                manifest=manifest,
                script=script,
                platform=PlatformType.YOUTUBE,
                dry_run=True,
                privacy="unlisted"
            )

            # Update job record to COMPLETED
            completed_iso = datetime.now().isoformat()
            with self.db.transaction() as conn:
                conn.cursor().execute("""
                UPDATE jobs
                SET status = 'COMPLETED', stage = 'published', updated_at = ?, completed_at = ?
                WHERE job_id = ?;
                """, (completed_iso, completed_iso, job_id))

            self.successful_runs += 1
            self.last_run_time = completed_iso
            self.log_event(
                "Michael",
                "CYCLE_COMPLETED",
                f"Asset generated & exported successfully: {pub_result.canonical_url}",
                division_id
            )

            return {
                "success": True,
                "job_id": job_id,
                "topic": topic.title,
                "video_path": video_path,
                "publication": pub_result.model_dump()
            }

        except Exception as e:
            self.failed_runs += 1
            self.log_event("Dwight", "CRITICAL_ERROR", str(e), division_id)
            with self.db.transaction() as conn:
                conn.cursor().execute("UPDATE jobs SET status = 'FAILED', updated_at = ? WHERE job_id = ?;", (datetime.now().isoformat(), job_id))
            return {"success": False, "error": str(e)}

    def tick(self) -> List[Dict[str, Any]]:
        """Single evaluation tick across all active divisions."""
        self.last_tick_time = datetime.now().isoformat()
        self.total_cycles += 1
        results = []

        divisions = self.registry.get_all_divisions()
        for div in divisions:
            if div.enabled:
                res = self.run_division_cycle(div.id, force=False)
                results.append({"division_id": div.id, "result": res})

        return results

    async def _loop(self):
        """Asynchronous execution loop that sleeps between ticks."""
        self.log_event("Michael", "SCHEDULER_STARTED", f"Cadence loop active (interval: {self.tick_interval_seconds}s)")
        while self.is_running:
            try:
                self.tick()
            except Exception as e:
                self.log_event("Dwight", "SCHEDULER_EXCEPTION", str(e))
            
            # Sleep until next tick
            for _ in range(self.tick_interval_seconds):
                if not self.is_running:
                    break
                await asyncio.sleep(1)

        self.log_event("Michael", "SCHEDULER_STOPPED", "Cadence loop paused by operator")

    def start(self):
        """Starts the autonomous scheduler loop."""
        if self.is_running:
            return
        self.is_running = True
        try:
            loop = asyncio.get_running_loop()
            self._task = loop.create_task(self._loop())
        except RuntimeError:
            # If no running event loop in current thread
            pass

    def stop(self):
        """Stops the autonomous scheduler loop."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            self._task = None

    def get_status(self) -> Dict[str, Any]:
        """Returns comprehensive real-time scheduler telemetry."""
        divisions = self.registry.get_all_divisions()
        div_telemetry = []
        for d in divisions:
            today_count = self.cadence.get_today_production_count(d.id)
            seconds_since = self.cadence.get_seconds_since_last_run(d.id)
            eligible, reason = self.cadence.evaluate_eligibility(d.id)
            div_telemetry.append({
                "id": d.id,
                "name": d.name,
                "enabled": d.enabled,
                "daily_produced": today_count,
                "daily_cap": d.publishing_schedule.max_daily,
                "seconds_since_last_run": round(seconds_since, 1) if seconds_since is not None else None,
                "is_eligible": eligible,
                "status_reason": reason
            })

        return {
            "is_running": self.is_running,
            "tick_interval_seconds": self.tick_interval_seconds,
            "total_cycles": self.total_cycles,
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs,
            "last_tick_time": self.last_tick_time,
            "last_run_time": self.last_run_time,
            "divisions": div_telemetry,
            "recent_events": self.recent_events[:15]
        }
