# Munder Difflin — Autonomous AI Business OS

> **A local-first, modular business operating system orchestrating multi-division digital content, visual distribution, digital products, and automation services on Windows 11 at ₹0 software budget.**

---

## 🏛️ System Overview

Munder Difflin is engineered as a high-resilience, event-driven operating system designed to run on a standard Windows 11 laptop with zero paid subscriptions, zero cloud microservice costs, and zero external binary dependencies.

### Key Capabilities
- **7 Configurable Business Divisions**: From AI Technology Media (YouTube Shorts & Instagram Reels) to Pinterest Visual Syndication, Science Education, Digital Product packaging, and B2B Automation Services.
- **₹0 Zero-Cost Media Pipeline**:
  - **FFmpeg 7.1** embedded via `imageio-ffmpeg` (runs in user space without requiring system administrative privileges or triggering corporate Group Policy blocks).
  - **Neural Text-to-Speech** via `edge-tts`, seamlessly bridged to the Windows Native Certificate Store using `truststore` (bypasses corporate SSL proxy inspection).
  - **Deterministic State Machine**: SQLite 3 with Write-Ahead Logging (`WAL`) mode, foreign key integrity, and persistent FIFO job queuing.
- **Human-in-the-Loop & Safety**:
  - **Supervised Mode**: All generated content pauses at `AWAITING_APPROVAL` until approved by the operator.
  - **Emergency Stop Killswitch**: Instant hardware/file flag (`config/emergency_stop.flag`) pausing all workers gracefully.
  - **Idempotency Safeguards**: SHA-256 topic-date hashing guarantees duplicate jobs are never created or published.

---

## 📁 Repository Structure

```
munder-difflin/
├── .env.example                     # Environment template (NO secrets checked in)
├── .gitignore                       # Ignores runtime databases, logs, assets, credentials
├── README.md                        # Project documentation and operational guide
├── requirements.txt                 # Pinned dependencies (imageio-ffmpeg, edge-tts, etc.)
├── cli.py                           # Master CLI entrypoint for all operator commands
│
├── config/                          # Configuration files
│   ├── divisions.yaml               # Definitions, schedules, and quotas for all 7 divisions
│   ├── system.yaml                  # System paths, quiet hours, default models
│   └── emergency_stop.flag          # Global pause trigger (created/deleted on demand)
│
├── core/                            # The Business OS Kernel
│   ├── __init__.py                  # Injects truststore SSL bridge
│   ├── database.py                  # SQLite connection, WAL mode, migrations
│   ├── models.py                    # Typed Pydantic data schemas (Job, Division, Asset)
│   ├── queue.py                     # Persistent FIFO job queue with state transitions
│   ├── registry.py                  # Division registry loader & validator
│   └── orchestrator.py              # Executive Business Manager & dispatch loops
│
├── scripts/                         # Operational & Bootstrap Scripts
│   └── verify_env.py                # 6-step environment diagnostic script
│
├── tests/                           # Verification Suite
│   └── test_kernel.py               # Unit & integration test suite (Phase 1 Acceptance)
│
└── data/                            # Persistent Runtime Data (Gitignored)
    ├── munder_difflin.db            # Master SQLite Database (WAL mode)
    ├── assets/                      # Generated MP4s, PNGs, SRTs per division
    ├── products/                    # Compiled digital products
    └── reports/                     # Daily executive summaries
```

---

## ⚡ Quickstart & Operational Commands

### 1. Verify Workstation Environment
Run the diagnostic suite to ensure Python, FFmpeg, Edge-TTS, and Windows Truststore are functional:
```powershell
py scripts/verify_env.py
```

### 2. View System Health and Queue Status
```powershell
py cli.py status
```

### 3. List Registered Business Divisions
```powershell
py cli.py divisions
```

### 4. Enqueue a Content Production Job
```powershell
py cli.py enqueue --division div_a_tech --topic "Building Autonomous Agents with Python"
```

### 5. Inspect the Persistent Job Queue
```powershell
py cli.py queue
```

### 6. Run Worker Against Queued Jobs
```powershell
py cli.py run-worker --once
```

### 7. Approve a Job for Publication
```powershell
py cli.py approve --job-id <job_id>
```

### 8. Emergency Stop Controls
Engage emergency stop (instantly pauses all production workers):
```powershell
py cli.py emergency-stop on
```
Disengage emergency stop (restores normal operations):
```powershell
py cli.py emergency-stop off
```

---

## 🧪 Automated Test Suite

Run the full Phase 1 Acceptance test suite covering database schema, WAL mode, division syncing, queue FIFO priority, idempotency deduplication, retry limits, approval flows, and emergency killswitch:
```powershell
py tests/test_kernel.py
```

---

## 🗺️ Roadmap Status

- [x] **Phase 0: Environment Diagnostic & Dependency Bootstrap**
  - Group Policy bypass via `imageio-ffmpeg` (embedded FFmpeg 7.1).
  - Corporate proxy SSL inspection bridge via `truststore`.
  - Neural TTS verified with `edge-tts`.
- [x] **Phase 1: Local Application Kernel, SQLite Database, Registry & Task Queue**
  - Persistent SQLite WAL queue with atomic transitions.
  - Division registry for all 7 business subsidiaries.
  - Master CLI (`cli.py`) with queue management, approvals, and emergency killswitch.
  - Automated acceptance test suite passed (`tests/test_kernel.py`).
- [ ] **Phase 2: Video Production Pipeline & Division A Local Video Generation**
  - Research Agent (ArXiv / GitHub Trending scraper).
  - Script Agent (Gemini free tier / structured JSON).
  - FFmpeg 9:16 vertical video composition + word-level SRT captions.
- [ ] **Phase 3: Official YouTube API Integration (OAuth + Upload)**
- [ ] **Phase 4: Official Instagram Reels Integration**
- [ ] **Phase 5: Pinterest Visual Distribution & Repurposing**
- [ ] **Phase 6: Windows Scheduler, Closed-loop Analytics & Financial Reporting**
- [ ] **Phase 7: Digital Products Engine (Division F)**
- [ ] **Phase 8: AI Automation Services Pipeline (Division G)**
- [ ] **Phase 9: Multi-Division Expansion (Divisions B, C, D)**
