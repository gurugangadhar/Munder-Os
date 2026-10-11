# 🏢 Munder Difflin — Autonomous AI Business OS

[![CI Verification](https://github.com/gurugangadhar/Munder-Os/actions/workflows/autonomous_ci.yml/badge.svg)](https://github.com/gurugangadhar/Munder-Os/actions/workflows/autonomous_ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Budget: ₹0](https://img.shields.io/badge/Budget-%E2%82%B90.00%20(Free%20Tier)-brightgreen.svg)]()
[![Platform: Windows 11](https://img.shields.io/badge/Platform-Windows%2011%20%7C%20Linux-orange.svg)]()

> **A local-first, modular autonomous business operating system orchestrating multi-division digital content, visual distribution, digital products, and client automation services at ₹0 software budget.**

---

## 🏛️ System Overview

Munder Difflin is engineered as an event-driven operating system designed to run on a standard Windows 11 workstation (or Linux cloud runner) with zero paid subscriptions, zero credit cards, and zero external binary installations.

### 🌟 Core Highlights
- **7 Independent Business Divisions**: From AI Technology Media (YouTube Shorts & Instagram Reels) to Pinterest Visual Syndication, Science Education, Children's Animation, Ambient Audio, Digital Products, and B2B Automation Services.
- **13 Specialized Autonomous AI Agents**: Staffed by authentic Dunder Mifflin personas (Michael, Jim, Dwight, Pam, Angela, Kevin, Ryan, Stanley, Creed, Oscar, Andy, Toby, Meredith) with genuine LLM deliberation.
- **Dual LLM Architecture**:
  - **Google Gemini** (`models/gemini-flash-lite-latest`) as primary real-time intelligence (~300ms latency).
  - **NVIDIA NIM DeepSeek** (`deepseek-ai/deepseek-coder-6.7b-instruct`) as automated failover.
- **Interactive 2D Scranton Floor Command Center**:
  - Tiled 2D Scranton office map with animated character avatars.
  - Active speech bubbles illuminate dynamically as agents speak.
  - 5 fully wired operational tabs: `terminal`, `workers`, `tasks`, `memory`, `activity`.
- **Zero-Cost Local Video Production Pipeline**:
  - **Embedded FFmpeg 7.1** via `imageio-ffmpeg` (runs in user-space without admin rights).
  - **Edge-TTS Neural Voiceover** with Windows native certificate inspection bypass via `truststore`.
  - **1080×1920 Vertical Kinetic Slides** rendered with Pillow and TrueType typography.
  - **Dwight's 5-Point Quality & Rights Audit** (-14 LUFS compliance, duration bounds, source verification).
- **Enterprise-Grade Safety & Reliability**:
  - SQLite Write-Ahead Logging (`WAL`) mode with persistent FIFO job queues.
  - Human-in-the-loop supervised approval gates.
  - Global Emergency Stop killswitch (`config/emergency_stop.flag`).
  - SHA-256 topic-date idempotency keys prevent duplicate generation or publishing.

---

## 🖥️ Scranton Command Center (Web UI)

Launch the real-time operational dashboard in your browser:

```powershell
py -m uvicorn dashboard.app:app --host 127.0.0.1 --port 8000
```
Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** to access the 5 Command Center tabs:

| Tab | Capability |
| :--- | :--- |
| **💻 terminal** | Live multi-agent console with color-coded dialogue bubbles and conference room meeting deliberation. Characters on the 2D floor physically illuminate as they speak. |
| **👥 workers** | Live status roster of all 13 agents (`ONLINE`, `ACTIVE`, `READY`, `STANDBY`). Includes 1-on-1 **Direct Message** modal to consult any individual agent in real time. |
| **📋 tasks** | Persistent SQLite FIFO job queue. Displays division tags, status pills, execution attempts, and includes a **"▶ Run Next Job"** action button. |
| **🧠 memory** | Live system state & knowledge inspector. Lists all 7 registered business divisions, Creed's scraped topics & arXiv citations, and Kevin's ₹0 financial balance sheet. |
| **⚡ activity** | System-wide audit log tracking every agent dispatch, direct message, pipeline stage, and conference deliberation with exact timestamps. |

---

## 📁 Repository Structure

```
munder-difflin/
├── .github/workflows/
│   └── autonomous_ci.yml            # Automated GitHub Actions test & LLM verification
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
│   ├── llm.py                       # Unified Gemini & NVIDIA NIM DeepSeek client
│   ├── models.py                    # Typed Pydantic data schemas (Job, Division, Asset)
│   ├── queue.py                     # Persistent FIFO job queue with atomic state transitions
│   ├── registry.py                  # Division registry loader & validator
│   ├── orchestrator.py              # Executive Business Manager & dispatch loops
│   │
│   ├── agents/                      # Multi-Agent Coordination Engine
│   │   └── conversation.py          # Conference deliberation, 1-on-1 chat, and event logging
│   │
│   └── media/                       # Zero-Cost Production Pipeline
│       ├── research.py              # Creed's verified open-source topic scraper
│       ├── scriptwriter.py          # Pam's 50s retention-optimized 5-scene scripts
│       ├── audio.py                 # Angela's Edge-TTS audio synthesizer & -14 LUFS QA
│       ├── visuals.py               # Ryan's 1080x1920 vertical kinetic slide generator
│       ├── compositor.py            # Stanley's FFmpeg video render & compositing engine
│       ├── qa.py                    # Dwight's 5-point quality and rights audit
│       └── pipeline.py              # Master multi-agent production orchestrator
│
├── dashboard/                       # Scranton Command Center Web Application
│   ├── app.py                       # FastAPI application serving REST endpoints & static files
│   ├── office_floor.html            # 2D Scranton map, character avatars & 5 command tabs
│   └── static/assets/characters/    # Pixel-art avatars for all 13 Office characters
│
├── scripts/                         # Operational & Bootstrap Scripts
│   ├── verify_env.py                # Environment diagnostic script
│   ├── sync_to_github.py            # REST API GitHub synchronization utility
│   ├── test_keys.py                 # API key probing utility for Gemini and NVIDIA
│   └── test_tabs.py                 # Automated integration test for all 5 web tabs
│
├── tests/                           # Verification Suite
│   └── test_kernel.py               # Unit & integration test suite (Phase 1 Acceptance)
│
└── data/                            # Persistent Runtime Data (Gitignored)
    ├── munder_difflin.db            # Master SQLite Database (WAL mode)
    └── output/division_a/           # Rendered 1080x1920 MP4 vertical video shorts
```

---

## ⚡ Quickstart & Local Execution

### 1. Configure Environment
Copy `.env.example` to `.env` and insert your free-tier keys:
```env
GEMINI_API_KEY=your_gemini_api_key_here
NVIDIA_API_KEY=your_nvidia_api_key_here
SUPERVISED_MODE=true
EMERGENCY_STOP=false
```

### 2. Verify Workstation Environment
Run the diagnostic suite to ensure Python, FFmpeg, Edge-TTS, and Windows Truststore are functional:
```powershell
py scripts/verify_env.py
```

### 3. Launch the Scranton Command Center
```powershell
py -m uvicorn dashboard.app:app --host 127.0.0.1 --port 8000
```
Navigate to **`http://127.0.0.1:8000`** in your browser.

### 4. Produce a Vertical Video Short via CLI
Produce an end-to-end 1080×1920 vertical video short for Division A:
```powershell
py -c "import asyncio; from core.media.pipeline import MediaProductionPipeline; asyncio.run(MediaProductionPipeline().produce_short('div_a_tech', 'tech_001_local_agents'))"
```
Output: Rendered MP4 in `data/output/division_a/` (~17 seconds render time, 1080×1920, ₹0.00 cost).

### 5. Run the Automated Kernel Test Suite
```powershell
py -m unittest tests/test_kernel.py
```

---

## 🔒 GitHub Actions CI/CD Cloud Verification

This repository is continuously tested using GitHub Actions:
- **Workflow**: [`.github/workflows/autonomous_ci.yml`](.github/workflows/autonomous_ci.yml)
- **Secrets Required**:
  - `GEMINI_API_KEY`: Set under `Settings -> Secrets and variables -> Actions`.
  - `NVIDIA_API_KEY`: Set under `Settings -> Secrets and variables -> Actions`.
- **Automated Checks**:
  1. Unit tests for SQLite WAL database, FIFO queue, idempotency, and killswitches.
  2. Multi-agent LLM inference test verifying Michael Scott's executive dialogue in the cloud.

---

## 🗺️ Roadmap & Phase Completion

- [x] **Phase 0: Environment Diagnostic & Dependency Bootstrap**
  - Windows DLP / Group Policy bypass via `imageio-ffmpeg` (embedded FFmpeg 7.1).
  - Corporate proxy SSL inspection bridge via `truststore`.
  - Zero-cost neural TTS verified with `edge-tts`.
- [x] **Phase 1: Local Application Kernel, SQLite Database, Registry & Task Queue**
  - Persistent SQLite WAL queue with atomic FIFO transitions.
  - Division registry for all 7 business subsidiaries.
  - Master CLI (`cli.py`) with queue management, approvals, and emergency killswitch.
  - Full automated acceptance test suite passed (`tests/test_kernel.py`).
- [x] **Phase 2: Zero-Cost Video Production Pipeline & Multi-Agent Intelligence**
  - Creed's topic research scraper with source validation and citations.
  - Pam's 50s retention-optimized scriptwriting engine (5-scene pacing).
  - Angela's audio QA & synthesis engine (-14 LUFS compliance).
  - Ryan's vertical 1080×1920 kinetic slide generator with Pillow and TrueType fonts.
  - Stanley's FFmpeg compositor rendering clean vertical MP4s.
  - Dwight's 5-point QA audit.
  - Kevin's financial ledger tracking ₹0.00 operational costs.
  - Google Gemini & NVIDIA NIM DeepSeek multi-agent deliberation engine.
  - Interactive Scranton Command Center with 5 active tabs (`terminal`, `workers`, `tasks`, `memory`, `activity`).
  - GitHub Actions CI/CD workflow with encrypted repository secrets.
- [ ] **Phase 3: Official YouTube API Integration (OAuth 2.0 + Uploads)**
- [ ] **Phase 4: Official Instagram Reels Integration**
- [ ] **Phase 5: Pinterest Visual Distribution & Repurposing**
- [ ] **Phase 6: Windows Scheduler, Closed-loop Analytics & Financial Reporting**
- [ ] **Phase 7: Digital Products Engine (Division F)**
- [ ] **Phase 8: AI Automation Services Pipeline (Division G)**
- [ ] **Phase 9: Multi-Division Expansion (Divisions B, C, D)**

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
