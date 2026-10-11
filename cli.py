"""
Munder Difflin — Master Command Line Interface (CLI)
Zero-friction operator controls for managing divisions, jobs, queues, and emergency stops.
"""

import sys
import os
import argparse
from datetime import datetime

# Safe stdout reconfigure for Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Ensure truststore SSL bridge is active
import truststore
truststore.inject_into_ssl()

from core.database import Database
from core.registry import DivisionRegistry
from core.queue import JobQueue
from core.orchestrator import Orchestrator
from core.models import JobStatus


def print_banner():
    print("=" * 70)
    print("  MUNDER DIFFLIN -- AUTONOMOUS AI BUSINESS OS")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Local Windows Mode")
    print("=" * 70)


def cmd_status(args):
    print_banner()
    orch = Orchestrator()
    health = orch.check_system_health()
    stats = orch.queue.get_queue_stats()

    status_tag = f"[{health.status}]"
    print(f"\nSystem Status: {status_tag}")
    print(f"Emergency Stop: {'ENGAGED (System Paused)' if health.emergency_stop_active else 'Disengaged (Operational)'}")
    print(f"Drive C: Free Space: {health.disk_free_gb} GB")
    print(f"Supervised Mode: {'Enabled (Manual review required)' if orch.config.get('system', {}).get('supervised_mode', True) else 'Disabled (Autonomous)'}")

    print("\nQueue Counters:")
    for status_name, count in stats.items():
        print(f"  - {status_name:20}: {count}")

    if health.issues:
        print("\nActive Alerts / Issues:")
        for issue in health.issues:
            print(f"  [!] {issue}")
    print()


def cmd_divisions(args):
    print_banner()
    reg = DivisionRegistry()
    divs = reg.get_all_divisions()

    print(f"\nRegistered Business Divisions ({len(divs)} total):\n")
    print(f"{'ID':<24} {'NAME':<30} {'STATUS':<10} {'PRIORITY':<8} {'DAILY TARGET'}")
    print("-" * 80)
    for d in divs:
        status_str = "ACTIVE" if d.enabled else "DISABLED"
        print(f"{d.id:<24} {d.name:<30} {status_str:<10} {d.priority:<8} {d.publishing_schedule.daily_target}/day")
    print()


def cmd_enqueue(args):
    print_banner()
    reg = DivisionRegistry()
    div = reg.get_division(args.division)
    if not div:
        print(f"[ERROR] Division '{args.division}' does not exist.")
        print("Use 'py cli.py divisions' to view valid division IDs.")
        sys.exit(1)

    queue = JobQueue()
    job = queue.enqueue(division_id=args.division, topic=args.topic)
    print(f"\n[OK] Job registered in persistent queue:")
    print(f"  Job ID         : {job.job_id}")
    print(f"  Division       : {div.name} ({div.id})")
    print(f"  Topic          : {job.topic}")
    print(f"  Idempotency Key: {job.idempotency_key}")
    print(f"  Current Status : {job.status.value}")
    print(f"  Stage          : {job.stage}\n")


def cmd_queue(args):
    print_banner()
    queue = JobQueue()
    filter_status = JobStatus(args.status) if args.status else None
    jobs = queue.list_jobs(status=filter_status, division_id=args.division, limit=args.limit)

    print(f"\nPersistent Job Queue ({len(jobs)} jobs shown):\n")
    if not jobs:
        print("  Queue is empty.")
    else:
        print(f"{'JOB ID':<18} {'DIVISION':<20} {'STATUS':<20} {'STAGE':<15} {'TOPIC'}")
        print("-" * 90)
        for j in jobs:
            print(f"{j.job_id:<18} {j.division_id:<20} {j.status.value:<20} {j.stage:<15} {j.topic[:30]}")
    print()


def cmd_approve(args):
    print_banner()
    queue = JobQueue()
    job = queue.get_job(args.job_id)
    if not job:
        print(f"[ERROR] Job ID '{args.job_id}' not found.")
        sys.exit(1)

    if job.status != JobStatus.AWAITING_APPROVAL:
        print(f"[WARN] Job '{args.job_id}' is in state '{job.status.value}', not AWAITING_APPROVAL.")
        print("Approval only applies to jobs waiting for operator confirmation.")
        sys.exit(1)

    updated = queue.approve_job(args.job_id)
    print(f"[OK] Job '{args.job_id}' approved! Status transitioned to: {updated.status.value}")


def cmd_emergency_stop(args):
    print_banner()
    orch = Orchestrator()
    action = args.action.lower()
    if action == "on":
        orch.set_emergency_stop(True)
        print("[EMERGENCY STOP] Flag set to ON. System is now PAUSED.")
    elif action == "off":
        orch.set_emergency_stop(False)
        print("[EMERGENCY STOP] Flag CLEARED. System is now OPERATIONAL.")
    else:
        is_active = orch.is_emergency_stop_active()
        print(f"Current Emergency Stop status: {'ENGAGED' if is_active else 'DISENGAGED'}")
        print("To change, run: 'py cli.py emergency-stop on' or 'py cli.py emergency-stop off'")


def cmd_run_worker(args):
    print_banner()
    orch = Orchestrator()
    if orch.is_emergency_stop_active():
        print("[ERROR] Cannot run worker: Emergency Stop is currently ENGAGED.")
        sys.exit(1)

    print("Running worker against persistent queue...")

    def mock_worker(job):
        print(f"  -> Processing Job: {job.job_id} [{job.division_id}] - '{job.topic}'")
        return {"status": "processed_by_kernel", "processed_at": datetime.now().isoformat()}

    count = 0
    while True:
        job = orch.run_next_job(mock_worker)
        if not job:
            if count == 0:
                print("  No eligible QUEUED jobs found.")
            else:
                print(f"  Queue drained. Processed {count} jobs.")
            break
        count += 1
        print(f"  [OK] Job {job.job_id} transitioned to: {job.status.value}")
        if args.once:
            break


def main():
    parser = argparse.ArgumentParser(description="Munder Difflin — Autonomous AI Business OS")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # status
    subparsers.add_parser("status", help="Show system health, queue counts, and disk status")

    # divisions
    subparsers.add_parser("divisions", help="List registered business divisions")

    # enqueue
    enq_parser = subparsers.add_parser("enqueue", help="Add a topic job to the queue")
    enq_parser.add_argument("--division", "-d", required=True, help="Division ID (e.g. div_a_tech)")
    enq_parser.add_argument("--topic", "-t", required=True, help="Topic description or headline")

    # queue
    q_parser = subparsers.add_parser("queue", help="Inspect persistent job queue")
    q_parser.add_argument("--status", "-s", choices=[s.value for s in JobStatus], help="Filter by status")
    q_parser.add_argument("--division", "-d", help="Filter by division ID")
    q_parser.add_argument("--limit", "-l", type=int, default=20, help="Max jobs to display")

    # approve
    app_parser = subparsers.add_parser("approve", help="Approve an AWAITING_APPROVAL job for publication")
    app_parser.add_argument("--job-id", "-j", required=True, help="Job ID to approve")

    # run-worker
    worker_parser = subparsers.add_parser("run-worker", help="Drain queued jobs")
    worker_parser.add_argument("--once", action="store_true", help="Process at most one job and exit")

    # emergency-stop
    stop_parser = subparsers.add_parser("emergency-stop", help="View or toggle emergency stop killswitch")
    stop_parser.add_argument("action", nargs="?", default="status", choices=["on", "off", "status"], help="Set to on, off, or view status")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "status": cmd_status,
        "divisions": cmd_divisions,
        "enqueue": cmd_enqueue,
        "queue": cmd_queue,
        "approve": cmd_approve,
        "run-worker": cmd_run_worker,
        "emergency-stop": cmd_emergency_stop
    }

    cmd_fn = commands.get(args.command)
    if cmd_fn:
        cmd_fn(args)


if __name__ == "__main__":
    main()
