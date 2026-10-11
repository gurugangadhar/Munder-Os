"""
Munder Difflin — Local Web Dashboard
Zero-dependency, high-contrast operational dashboard running on FastAPI.
Accessible locally at http://127.0.0.1:8000
"""

import sys
import os

# Ensure truststore SSL bridge and project root
import truststore
truststore.inject_into_ssl()
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
import uvicorn
from datetime import datetime

from core.database import Database
from core.registry import DivisionRegistry
from core.queue import JobQueue
from core.orchestrator import Orchestrator
from core.models import JobStatus

from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Munder Difflin Business OS")
db = Database()
registry = DivisionRegistry(db=db)
queue = JobQueue(db=db)
orchestrator = Orchestrator(db=db, queue=queue, registry=registry)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/office-map", response_class=HTMLResponse)
def get_office_map():
    map_path = os.path.join(os.path.dirname(__file__), "office_floor.html")
    if os.path.exists(map_path):
        with open(map_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Office floor map not found</h1>", status_code=404)


@app.get("/", response_class=HTMLResponse)
def get_dashboard_root():
    return get_office_map()


@app.get("/classic", response_class=HTMLResponse)
def get_dashboard(request: Request):
    health = orchestrator.check_system_health()
    divisions = registry.get_all_divisions()
    jobs = queue.list_jobs(limit=25)
    stats = queue.get_queue_stats()
    emergency_active = orchestrator.is_emergency_stop_active()

    status_color = "#ef4444" if emergency_active or health.status == "CRITICAL" else "#10b981"
    status_text = "EMERGENCY PAUSED" if emergency_active else health.status

    # Build Division Cards HTML
    div_cards_html = ""
    for d in divisions:
        active_badge = (
            '<span style="background: #064e3b; color: #34d399; padding: 2px 8px; border-radius: 9999px; font-size: 11px; font-weight: 600;">ACTIVE</span>'
            if d.enabled else
            '<span style="background: #374151; color: #9ca3af; padding: 2px 8px; border-radius: 9999px; font-size: 11px; font-weight: 600;">STANDBY</span>'
        )
        platforms_html = " ".join([f'<span style="background: #1f2937; color: #e5e7eb; padding: 2px 6px; border-radius: 4px; font-size: 11px;">{p.name.value}:{p.format}</span>' for p in d.platforms])
        
        div_cards_html += f"""
        <div style="background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 16px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 11px; font-family: monospace; color: #38bdf8;">{d.id}</span>
                    {active_badge}
                </div>
                <h3 style="margin: 0 0 6px 0; font-size: 15px; color: #f8fafc; font-weight: 600;">{d.name}</h3>
                <p style="margin: 0 0 12px 0; font-size: 12px; color: #94a3b8; line-height: 1.4;">{d.description}</p>
            </div>
            <div>
                <div style="margin-bottom: 8px;">{platforms_html}</div>
                <div style="display: flex; justify-content: space-between; font-size: 11px; color: #64748b; border-top: 1px solid #334155; padding-top: 8px;">
                    <span>Priority: <b>{d.priority}</b></span>
                    <span>Target: <b>{d.publishing_schedule.daily_target}/day</b></span>
                </div>
            </div>
        </div>
        """

    # Build Queue Rows HTML
    queue_rows_html = ""
    if not jobs:
        queue_rows_html = '<tr><td colspan="6" style="padding: 24px; text-align: center; color: #64748b;">No jobs in queue yet. Use the Enqueue button above to start one!</td></tr>'
    else:
        for j in jobs:
            badge_color = {
                "QUEUED": "#3b82f6",
                "PROCESSING": "#f59e0b",
                "AWAITING_APPROVAL": "#ec4899",
                "READY_FOR_PUBLISH": "#8b5cf6",
                "COMPLETED": "#10b981",
                "FAILED": "#ef4444",
                "CANCELLED": "#6b7280"
            }.get(j.status.value, "#64748b")

            approve_btn = ""
            if j.status == JobStatus.AWAITING_APPROVAL:
                approve_btn = f"""
                <form method="POST" action="/approve" style="display: inline;">
                    <input type="hidden" name="job_id" value="{j.job_id}">
                    <button type="submit" style="background: #10b981; color: white; border: none; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 600; cursor: pointer;">Approve</button>
                </form>
                """

            queue_rows_html += f"""
            <tr style="border-bottom: 1px solid #334155;">
                <td style="padding: 10px; font-family: monospace; font-size: 12px; color: #94a3b8;">{j.job_id}</td>
                <td style="padding: 10px; font-size: 12px; color: #38bdf8;">{j.division_id}</td>
                <td style="padding: 10px; font-size: 13px; color: #f1f5f9; max-width: 280px;">{j.topic}</td>
                <td style="padding: 10px;">
                    <span style="background: {badge_color}22; color: {badge_color}; border: 1px solid {badge_color}55; padding: 2px 8px; border-radius: 9999px; font-size: 11px; font-weight: 600;">
                        {j.status.value}
                    </span>
                </td>
                <td style="padding: 10px; font-size: 11px; color: #64748b; font-family: monospace;">{j.stage}</td>
                <td style="padding: 10px; text-align: right;">{approve_btn}</td>
            </tr>
            """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Munder Difflin — Autonomous AI Business OS</title>
        <style>
            * {{ box-sizing: border-box; }}
            body {{
                margin: 0;
                padding: 24px;
                background-color: #0b0f19;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                color: #f8fafc;
            }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: #111827;
                border: 1px solid #1f2937;
                border-radius: 12px;
                padding: 16px 24px;
                margin-bottom: 24px;
            }}
            .btn {{
                background: #2563eb;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
            }}
            .btn:hover {{ background: #1d4ed8; }}
            .btn-danger {{ background: #dc2626; }}
            .btn-danger:hover {{ background: #b91c1c; }}
            .btn-success {{ background: #16a34a; }}
            .btn-success:hover {{ background: #15803d; }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 16px;
                margin-bottom: 24px;
            }}
            .stat-card {{
                background: #111827;
                border: 1px solid #1f2937;
                border-radius: 8px;
                padding: 16px;
            }}
            .section-title {{
                font-size: 18px;
                font-weight: 700;
                color: #f8fafc;
                margin: 24px 0 12px 0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .divisions-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
                gap: 16px;
                margin-bottom: 32px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background: #111827;
                border: 1px solid #1f2937;
                border-radius: 8px;
                overflow: hidden;
            }}
            th {{
                background: #1f2937;
                color: #94a3b8;
                font-size: 12px;
                font-weight: 600;
                text-align: left;
                padding: 12px 10px;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }}
            input, select {{
                background: #1f2937;
                border: 1px solid #374151;
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Header -->
            <div class="header">
                <div>
                    <h1 style="margin: 0; font-size: 22px; font-weight: 800; letter-spacing: -0.02em; color: #ffffff;">
                        Munder Difflin <span style="font-size: 14px; font-weight: 500; color: #38bdf8;">Autonomous Business OS</span>
                    </h1>
                    <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">
                        Windows 11 Workstation | Status: <b style="color: {status_color};">{status_text}</b> | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    </div>
                </div>
                <div style="display: flex; gap: 10px;">
                    <form method="POST" action="/toggle-emergency">
                        <button type="submit" class="btn {'btn-success' if emergency_active else 'btn-danger'}">
                            {'Disengage Emergency Stop' if emergency_active else 'Engage Emergency Stop'}
                        </button>
                    </form>
                    <a href="/" class="btn" style="background: #374151;">Refresh</a>
                </div>
            </div>

            <!-- Health & Hardware Metric Cards -->
            <div class="stats-grid">
                <div class="stat-card">
                    <div style="font-size: 12px; color: #94a3b8;">Software Budget</div>
                    <div style="font-size: 24px; font-weight: 800; color: #34d399; margin-top: 4px;">₹0.00</div>
                    <div style="font-size: 11px; color: #64748b; margin-top: 4px;">Zero-Cost Verified</div>
                </div>
                <div class="stat-card">
                    <div style="font-size: 12px; color: #94a3b8;">Drive C: Free Space</div>
                    <div style="font-size: 24px; font-weight: 800; color: #38bdf8; margin-top: 4px;">{health.disk_free_gb} GB</div>
                    <div style="font-size: 11px; color: #64748b; margin-top: 4px;">Min threshold: 5.0 GB</div>
                </div>
                <div class="stat-card">
                    <div style="font-size: 12px; color: #94a3b8;">Queued Jobs</div>
                    <div style="font-size: 24px; font-weight: 800; color: #f59e0b; margin-top: 4px;">{stats.get('QUEUED', 0)}</div>
                    <div style="font-size: 11px; color: #64748b; margin-top: 4px;">Ready for worker</div>
                </div>
                <div class="stat-card">
                    <div style="font-size: 12px; color: #94a3b8;">Awaiting Approval</div>
                    <div style="font-size: 24px; font-weight: 800; color: #ec4899; margin-top: 4px;">{stats.get('AWAITING_APPROVAL', 0)}</div>
                    <div style="font-size: 11px; color: #64748b; margin-top: 4px;">Supervised Mode Active</div>
                </div>
                <div class="stat-card">
                    <div style="font-size: 12px; color: #94a3b8;">Ready to Publish</div>
                    <div style="font-size: 24px; font-weight: 800; color: #a855f7; margin-top: 4px;">{stats.get('READY_FOR_PUBLISH', 0)}</div>
                    <div style="font-size: 11px; color: #64748b; margin-top: 4px;">Approved by Operator</div>
                </div>
            </div>

            <!-- Virtual 2D Pixel-Art Office Floor -->
            <div class="section-title">
                <span>The Virtual Office Floor (Scranton HQ)</span>
                <span style="font-size: 13px; font-weight: 450; color: #94a3b8;">Click any employee to inspect dossier</span>
            </div>
            <div style="margin-bottom: 32px; background: #0f172a; border: 1px solid #1e293b; border-radius: 12px; padding: 12px; display: flex; justify-content: center; overflow-x: auto;">
                <iframe src="/office-map" style="width: 100%; min-width: 980px; height: 630px; border: none; border-radius: 8px;"></iframe>
            </div>

            <!-- Business Division Registry -->
            <div class="section-title">
                <span>Business Divisions (The Office Floor)</span>
                <span style="font-size: 13px; font-weight: 450; color: #94a3b8;">7 Autonomous Units</span>
            </div>
            <div class="divisions-grid">
                {div_cards_html}
            </div>

            <!-- Job Enqueue & Persistent Queue Section -->
            <div class="section-title">
                <span>Persistent Production Queue</span>
            </div>

            <!-- Quick Enqueue Form -->
            <div style="background: #111827; border: 1px solid #1f2937; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <form method="POST" action="/enqueue" style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
                    <select name="division_id" required style="flex: 1; min-width: 200px;">
                        <option value="div_a_tech">Division A: AI & Technology Media (Active)</option>
                        <option value="div_e_pinterest">Division E: Pinterest & Visual Distribution (Active)</option>
                        <option value="div_f_digital_products">Division F: Digital Products (Active)</option>
                        <option value="div_b_science">Division B: Science & Space Education (Standby)</option>
                        <option value="div_c_kids">Division C: Children's Animation (Standby)</option>
                        <option value="div_d_ambient">Division D: Ambient Media (Standby)</option>
                        <option value="div_g_services">Division G: AI Automation Services (Standby)</option>
                    </select>
                    <input type="text" name="topic" placeholder="Enter content topic or campaign idea..." required style="flex: 2; min-width: 300px;">
                    <button type="submit" class="btn">Enqueue Job</button>
                    <a href="/run-worker" class="btn btn-success" style="padding: 8px 14px;">Run Worker (1 Job)</a>
                </form>
            </div>

            <!-- Queue Table -->
            <table>
                <thead>
                    <tr>
                        <th>Job ID</th>
                        <th>Division</th>
                        <th>Topic</th>
                        <th>Status</th>
                        <th>Stage</th>
                        <th style="text-align: right;">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {queue_rows_html}
                </tbody>
            </table>

            <div style="margin-top: 32px; text-align: center; font-size: 12px; color: #475569;">
                Munder Difflin Autonomous Business OS &bull; Local-First Architecture &bull; SQLite WAL Persistent State
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/enqueue")
def handle_enqueue(division_id: str = Form(...), topic: str = Form(...)):
    queue.enqueue(division_id=division_id, topic=topic)
    return RedirectResponse(url="/", status_code=303)


@app.post("/approve")
def handle_approve(job_id: str = Form(...)):
    queue.approve_job(job_id)
    return RedirectResponse(url="/", status_code=303)


@app.post("/toggle-emergency")
def handle_toggle_emergency():
    active = orchestrator.is_emergency_stop_active()
    orchestrator.set_emergency_stop(not active)
    return RedirectResponse(url="/", status_code=303)


@app.get("/run-worker")
def handle_run_worker():
    def mock_worker(job):
        return {"status": "processed", "timestamp": datetime.now().isoformat()}
    orchestrator.run_next_job(mock_worker)
    return RedirectResponse(url="/", status_code=303)


def main():
    print("=" * 70)
    print("  Starting Munder Difflin Local Dashboard at: http://127.0.0.1:8000")
    print("  Press CTRL+C in this terminal to stop the server.")
    print("=" * 70)
    uvicorn.run("dashboard.app:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
