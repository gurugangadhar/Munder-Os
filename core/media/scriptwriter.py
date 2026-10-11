"""
Munder Difflin — Pam's Script & Copy Agent
Drafts 50-second retention-optimized video scripts with scene breakdown,
visual prompts, and platform metadata for YouTube Shorts and Instagram Reels.
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from core.media.research import TopicIdea


@dataclass
class VideoScene:
    scene_index: int
    duration_est_sec: float
    spoken_text: str
    headline: str
    subtext: str
    accent_color: str


@dataclass
class ProductionScript:
    title: str
    division_id: str
    scenes: List[VideoScene]
    full_narration: str
    youtube_metadata: Dict[str, Any]
    instagram_metadata: Dict[str, Any]


class ScriptAgent:
    """Pam Beesly — Scriptwriting & Platform Copy Agent."""

    def draft_script(self, topic: TopicIdea) -> ProductionScript:
        """Transforms a research topic into a synchronized multi-scene production script."""
        scenes = [
            VideoScene(
                scene_index=1,
                duration_est_sec=6.0,
                spoken_text=topic.hook,
                headline="LOCAL AI SECRETS",
                subtext="100% Free • Zero Subscriptions",
                accent_color="#38bdf8"
            ),
            VideoScene(
                scene_index=2,
                duration_est_sec=11.0,
                spoken_text=topic.core_points[0],
                headline="01 // OLLAMA",
                subtext="Run Llama 3 & DeepSeek Locally",
                accent_color="#10b981"
            ),
            VideoScene(
                scene_index=3,
                duration_est_sec=11.0,
                spoken_text=topic.core_points[1],
                headline="02 // AIDER & ANTIGRAVITY",
                subtext="Terminal AI Pair Programming",
                accent_color="#f59e0b"
            ),
            VideoScene(
                scene_index=4,
                duration_est_sec=11.0,
                spoken_text=topic.core_points[2],
                headline="03 // CONTINUE.DEV",
                subtext="Open-Source VS Code Autopilot",
                accent_color="#8b5cf6"
            ),
            VideoScene(
                scene_index=5,
                duration_est_sec=7.0,
                spoken_text=topic.call_to_action,
                headline="MUNDER DIFFLIN",
                subtext="Autonomous AI Business OS",
                accent_color="#ef4444"
            )
        ]

        full_narration = " ".join([s.spoken_text for s in scenes])

        youtube_metadata = {
            "title": f"{topic.title} #Shorts",
            "description": (
                f"{topic.title}\n\n"
                f"Discover how to run powerful AI agents locally on your computer with zero monthly subscriptions.\n\n"
                f"Featured Tools:\n"
                f"1. Ollama (Local Model Runner)\n"
                f"2. Aider & Antigravity (Terminal Pair Programmer)\n"
                f"3. Continue.dev (VS Code Copilot)\n\n"
                f"Built autonomously by Munder Difflin AI Business OS.\n"
                f"#AI #LocalAI #Ollama #Coding #Shorts #Automation #Technology"
            ),
            "tags": ["AI", "Local AI", "Ollama", "Coding Agent", "Antigravity", "Open Source", "Software Engineering", "Shorts"],
            "category_id": "28"  # Science & Technology
        }

        instagram_metadata = {
            "caption": (
                f"🚀 {topic.title}\n\n"
                f"Stop burning cash on monthly AI subscriptions. Your laptop can already run state-of-the-art agents for free.\n\n"
                f"Drop a comment with your favorite local tool below! 💬\n\n"
                f"#aicoding #localai #devtools #programmerlife #munderdifflin #techreels #openSource"
            ),
            "share_to_feed": True
        }

        return ProductionScript(
            title=topic.title,
            division_id="div_a_tech",
            scenes=scenes,
            full_narration=full_narration,
            youtube_metadata=youtube_metadata,
            instagram_metadata=instagram_metadata
        )
