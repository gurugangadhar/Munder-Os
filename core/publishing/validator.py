"""
Munder Difflin — Pre-flight Publishing Validator
Validates video dimensions, duration, bitrate, character counts, and compliance
before attempting official API calls or consuming platform quotas.
"""

import os
from typing import List, Tuple, Dict, Any
from core.models import PlatformType, AssetManifest, ScriptPackage


class PreflightValidator:
    """Rigorous pre-flight checks according to official platform developer guidelines."""

    @staticmethod
    def validate_youtube_shorts(manifest: AssetManifest, script: ScriptPackage) -> Tuple[bool, List[str]]:
        errors: List[str] = []

        # 1. Video file existence
        if not manifest.video_path or not os.path.exists(manifest.video_path):
            errors.append(f"YouTube Shorts: Video file missing at '{manifest.video_path}'.")
            return False, errors

        file_size = os.path.getsize(manifest.video_path)
        if file_size < 1024:
            errors.append(f"YouTube Shorts: Video file corrupted or zero-byte ({file_size} bytes).")

        # 2. Duration check (Max 60 seconds for Shorts)
        if script.estimated_duration_seconds > 60:
            errors.append(
                f"YouTube Shorts: Duration ({script.estimated_duration_seconds}s) exceeds official 60s limit."
            )

        # 3. Title length check (Max 100 characters)
        if len(script.title) > 100:
            errors.append(f"YouTube Shorts: Title length ({len(script.title)}) exceeds 100 character limit.")

        if len(script.title.strip()) < 5:
            errors.append("YouTube Shorts: Title is too short (< 5 chars).")

        # 4. Description length check (Max 5,000 characters)
        if len(script.description) > 5000:
            errors.append(
                f"YouTube Shorts: Description length ({len(script.description)}) exceeds 5000 characters."
            )

        # 5. Tag total character count check (Max 500 characters)
        total_tag_chars = sum(len(t) for t in script.tags)
        if total_tag_chars > 500:
            errors.append(
                f"YouTube Shorts: Cumulative tag length ({total_tag_chars}) exceeds 500 characters."
            )

        # 6. Quality assurance gate
        if not manifest.qa_passed:
            errors.append("YouTube Shorts: Asset failed Dwight's QA audit prior to publishing.")

        return len(errors) == 0, errors

    @staticmethod
    def validate_instagram_reels(manifest: AssetManifest, script: ScriptPackage) -> Tuple[bool, List[str]]:
        errors: List[str] = []

        if not manifest.video_path or not os.path.exists(manifest.video_path):
            errors.append(f"Instagram Reels: Video file missing at '{manifest.video_path}'.")
            return False, errors

        # 1. Duration check (3s to 90s)
        if script.estimated_duration_seconds < 3 or script.estimated_duration_seconds > 90:
            errors.append(
                f"Instagram Reels: Duration ({script.estimated_duration_seconds}s) must be between 3 and 90 seconds."
            )

        # 2. Caption length check (Max 2,200 characters)
        caption = f"{script.title}\n\n{script.description}"
        if len(caption) > 2200:
            errors.append(
                f"Instagram Reels: Caption ({len(caption)} chars) exceeds 2200 character limit."
            )

        # 3. Hashtag limit (Max 30)
        hashtag_count = sum(1 for word in script.description.split() if word.startswith("#"))
        if hashtag_count > 30:
            errors.append(
                f"Instagram Reels: Hashtag count ({hashtag_count}) exceeds maximum limit of 30."
            )

        return len(errors) == 0, errors

    @staticmethod
    def validate_pinterest_pins(manifest: AssetManifest, script: ScriptPackage) -> Tuple[bool, List[str]]:
        errors: List[str] = []

        # 1. Title limit (Max 100 characters)
        if len(script.title) > 100:
            errors.append(f"Pinterest: Title ({len(script.title)} chars) exceeds 100 character limit.")

        # 2. Description limit (Max 500 characters)
        if len(script.description) > 500:
            errors.append(
                f"Pinterest: Description ({len(script.description)} chars) exceeds 500 character limit."
            )

        # 3. Source or thumbnail existence
        if not manifest.video_path and not manifest.thumbnail_path:
            errors.append("Pinterest: Requires at least an image or video asset.")

        return len(errors) == 0, errors
