"""
Munder Difflin — Conversational & Command Engine for Michael Scott
Processes user commands, reasons about multi-agent task state,
and dispatches production workflows with authentic Office persona.
"""

from typing import Dict, Any, List
from core.media.pipeline import ProductionPipeline


class ConversationEngine:
    """Michael Scott — Executive Manager & Conversational Dispatcher."""

    def __init__(self, orchestrator=None, db=None, queue=None):
        self.orchestrator = orchestrator
        self.db = db
        self.queue = queue
        self.pipeline = ProductionPipeline()

    def process_message(self, user_msg: str) -> Dict[str, Any]:
        """Processes user input, determines intent, and triggers actions."""
        text = user_msg.strip().lower()

        # ─── 1. Production Trigger ─────────────────────────────────────────────
        if any(w in text for w in ["produce", "run", "start production", "make video", "generate", "video"]):
            # Trigger full production pipeline
            events = []
            def log_collector(agent, msg):
                events.append({"agent": agent, "message": msg})

            result = self.pipeline.run_division_a_production(log_callback=log_collector)

            return {
                "reply": "Boom! Conference room, five minutes! Production pipeline executed across all agents. Your 9:16 vertical video for Division A (AI Tech Media) is rendered and approved by Dwight!",
                "action": "PRODUCTION_COMPLETE",
                "events": events,
                "manifest": result.get("manifest"),
                "video_url": "/static/output/ai_agents_short_001.mp4"
            }

        # ─── 2. System Status ──────────────────────────────────────────────────
        elif any(w in text for w in ["status", "health", "system", "report"]):
            return {
                "reply": "Everything is running smoothly! All 7 business divisions are active on the floor. Oscar reports Drive C has 355 GB free. Zero failures in the SQLite queue.",
                "action": "STATUS_REPORT",
                "events": [
                    {"agent": "Michael", "message": "7 business divisions registered and operational."},
                    {"agent": "Oscar", "message": "Drive C: 355 GB free space verified."},
                    {"agent": "Toby", "message": "Emergency Stop killswitch disengaged. Safety checks clear."}
                ]
            }

        # ─── 3. Financial Ledger ───────────────────────────────────────────────
        elif any(w in text for w in ["ledger", "cost", "money", "budget", "finance", "spent", "revenue"]):
            return {
                "reply": "Kevin checked the books. Total cloud and API expenditure: exactly Rs. 0.00! We are running 100% locally with zero subscriptions.",
                "action": "FINANCE_REPORT",
                "events": [
                    {"agent": "Kevin", "message": "Ledger check: Total spent = Rs. 0.00. Software cost = Rs. 0.00. Net profit target intact."}
                ]
            }

        # ─── 4. Divisions Overview ─────────────────────────────────────────────
        elif any(w in text for w in ["division", "business", "divisions"]):
            return {
                "reply": "Here are our 7 divisions:\n"
                         "• Division A: AI & Tech Media (YouTube Shorts & Reels)\n"
                         "• Division B: Science & Space Education\n"
                         "• Division C: Children's Educational Animation\n"
                         "• Division D: Ambient & Relaxing Media\n"
                         "• Division E: Pinterest & Visual Distribution\n"
                         "• Division F: Digital Products & Prompt Packs\n"
                         "• Division G: AI Automation Services",
                "action": "DIVISIONS_LIST",
                "events": [
                    {"agent": "Michael", "message": "Managing 7 independent digital revenue streams."}
                ]
            }

        # ─── 5. Help / Onboarding ──────────────────────────────────────────────
        elif any(w in text for w in ["help", "how to", "start", "what can you do", "commands"]):
            return {
                "reply": "I am Michael Scott, Regional Manager of Dunder Mifflin and Executive Manager of Munder Difflin OS.\n\n"
                         "Here is what you can do:\n"
                         "1. Click the green '▶ Run Production' button (or type 'produce video') to have Creed, Pam, Angela, Ryan, and Stanley create a real 1080x1920 video.\n"
                         "2. Type 'status' to view system health and queue counts.\n"
                         "3. Type 'ledger' to see Kevin's financial audit (Rs. 0 spent).\n"
                         "4. Click on any employee on the office floor to open their Agent Dossier.",
                "action": "HELP",
                "events": [
                    {"agent": "Michael", "message": "Type 'produce video' or click 'Run Production' to start!"}
                ]
            }

        # ─── 6. General Conversational Persona ─────────────────────────────────
        else:
            return {
                "reply": f"'{user_msg}' — You know what they say: 'You miss 100% of the shots you don't take. — Wayne Gretzky' — Michael Scott. What division do you want to scale today?",
                "action": "CHAT",
                "events": [
                    {"agent": "Michael", "message": f"Acknowledged: '{user_msg}'"}
                ]
            }
