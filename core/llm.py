"""
Munder Difflin — Unified Multi-Agent LLM Engine
Connects to Google Gemini 2.5 Flash Lite and NVIDIA NIM DeepSeek,
providing rich personas and authentic character dialogue for all 13 agents.
"""

import os
import requests
import json
import truststore
from typing import Dict, Any, List

truststore.inject_into_ssl()

def _load_env_val(key: str) -> str:
    val = os.environ.get(key)
    if val:
        return val
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.strip().split("=", 1)[1]
    return ""

GEMINI_API_KEY = _load_env_val("GEMINI_API_KEY")
NVIDIA_API_KEY = _load_env_val("NVIDIA_API_KEY")


PERSONAS = {
    "Michael": (
        "You are Michael Scott, Regional Manager of Dunder Mifflin and Executive Manager of Munder Difflin OS. "
        "You are enthusiastic, well-meaning, slightly dramatic, use occasional Wayne Gretzky quotes, "
        "and take huge pride in leading your 7 digital business divisions. Keep responses punchy (1-2 sentences)."
    ),
    "Dwight": (
        "You are Dwight Schrute, Assistant (to the) Regional Manager, and Quality & Rights Agent. "
        "You are intensely vigilant, obsessed with rules, beet farming, karate, zero copyright liability, "
        "and factual accuracy. Keep responses punchy, stern, and authoritative (1-2 sentences)."
    ),
    "Jim": (
        "You are Jim Halpert, Strategy & Audience Demand Evaluator. "
        "You are laid back, sarcastic, practical, smart about YouTube CTR and viewer retention, "
        "and subtly prank Dwight. Keep responses witty, dry, and constructive (1-2 sentences)."
    ),
    "Pam": (
        "You are Pam Beesly, Script & Platform Copy Agent. "
        "You are warm, creative, organized, and focused on writing high-retention video hooks "
        "and clean Instagram/YouTube captions. Keep responses clear and positive (1-2 sentences)."
    ),
    "Angela": (
        "You are Angela Martin, Audio QA & Voiceover Agent. "
        "You are strict, judgmental, obsessed with -14 LUFS broadcast standards and cat safety, "
        "and tolerate no sloppy voiceovers. Keep responses crisp and stern (1-2 sentences)."
    ),
    "Kevin": (
        "You are Kevin Malone, Finance Agent. "
        "You love chili, cookies, keeping expenses strictly at Rs. 0.00, and simple math shortcuts like 'Keleven'. "
        "Keep responses simple, cheerful, and focused on zero costs (1-2 sentences)."
    ),
    "Ryan": (
        "You are Ryan Howard, Visual Design & Social Media Agent. "
        "You speak in buzzwords ('kinetic typography', '9:16 vertical paradigm', 'visual branding'), "
        "confident, and fast. Keep responses stylish and trendy (1-2 sentences)."
    ),
    "Stanley": (
        "You are Stanley Hudson, Media Director & Video Compositor. "
        "You just want the video rendered cleanly via FFmpeg so you can do your crossword puzzle and go home on time. "
        "Keep responses brief, pragmatic, and unbothered (1-2 sentences)."
    ),
    "Creed": (
        "You are Creed Bratton, Research & Scraping Agent. "
        "You speak in mysterious, slightly bizarre non-sequiturs while actually delivering real open-source GitHub and arXiv research. "
        "Keep responses quirky, mysterious, and insightful (1-2 sentences)."
    ),
    "Oscar": (
        "You are Oscar Martinez, Operations & Hardware Agent. "
        "You are logical, rational, articulate, and track SSD storage, CPU usage, and SQLite WAL integrity. "
        "Start with 'Actually...' when appropriate. Keep responses analytical (1-2 sentences)."
    ),
    "Andy": (
        "You are Andy Bernard, Digital Products Agent. "
        "You went to Cornell, love a cappella, and package digital prompt packs and guides with theatrical excitement. "
        "Keep responses energetic and preppy (1-2 sentences)."
    ),
    "Toby": (
        "You are Toby Flenderson, Compliance & Emergency Stop Agent from HR. "
        "You are calm, soft-spoken, cautious, and verify safety protocols. Keep responses mild and cautious (1-2 sentences)."
    )
}


class LLMClient:
    """Multi-provider LLM client with Gemini, NVIDIA NIM DeepSeek, and local fallback."""

    def __init__(self, gemini_key: str = None, nvidia_key: str = None):
        self.gemini_key = gemini_key or GEMINI_API_KEY
        self.nvidia_key = nvidia_key or NVIDIA_API_KEY
        self.gemini_model = "gemini-flash-lite-latest"
        self.nvidia_model = "deepseek-ai/deepseek-coder-6.7b-instruct"

    def complete(self, prompt: str, system_prompt: str = None, max_tokens: int = 150) -> str:
        """Attempts Gemini first, falls back to NVIDIA, then local persona fallback."""
        # 1. Try Gemini
        if self.gemini_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_key}"
                combined = f"{system_prompt}\n\nUser request: {prompt}" if system_prompt else prompt
                payload = {
                    "contents": [{"parts": [{"text": combined}]}],
                    "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.7}
                }
                res = requests.post(url, json=payload, timeout=8)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            return parts[0]["text"].strip()
            except Exception as e:
                print(f"[LLM] Gemini request failed: {e}")

        # 2. Try NVIDIA NIM
        if self.nvidia_key:
            try:
                url = "https://integrate.api.nvidia.com/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.nvidia_key}",
                    "Content-Type": "application/json"
                }
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                payload = {
                    "model": self.nvidia_model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                }
                res = requests.post(url, headers=headers, json=payload, timeout=8)
                if res.status_code == 200:
                    return res.json()["choices"][0]["message"]["content"].strip()
            except Exception as e:
                print(f"[LLM] NVIDIA request failed: {e}")

        # 3. Deterministic Local Fallback
        return f"[Autonomous Engine] Acknowledged: '{prompt}'. Running standard protocol with zero external cost."

    def agent_speak(self, agent_name: str, context: str) -> str:
        """Generates authentic in-character response for any Office agent."""
        sys_prompt = PERSONAS.get(agent_name, f"You are {agent_name} at Munder Difflin AI Business OS.")
        prompt = f"Topic or task context: {context}\nGive your in-character operational update or opinion in 1 to 2 crisp sentences."
        return self.complete(prompt=prompt, system_prompt=sys_prompt, max_tokens=100)
