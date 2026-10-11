"""
Munder Difflin — Official Pinterest API v5 Publisher
Handles validation, Board assignment, video/image pin creation,
and dry-run export packages.
"""

import os
import json
import shutil
from typing import Dict, Any, Tuple, List
from datetime import datetime
from core.models import PlatformType, AssetManifest, ScriptPackage
from core.publishing.base import BasePublisher, PublishResult
from core.publishing.validator import PreflightValidator


EXPORTS_DIR = "data/exports/pinterest"
CREDENTIALS_FILE = "config/pinterest_token.json"


class PinterestPublisher(BasePublisher):
    """Pinterest API v5 Pin and Video Pin publisher."""

    def __init__(self, credentials_path: str = CREDENTIALS_FILE):
        super().__init__(PlatformType.PINTEREST)
        self.credentials_path = credentials_path
        os.makedirs(EXPORTS_DIR, exist_ok=True)

    def validate(self, manifest: AssetManifest, script: ScriptPackage) -> Tuple[bool, List[str]]:
        return PreflightValidator.validate_pinterest_pins(manifest, script)

    def is_authenticated(self) -> bool:
        if not os.path.exists(self.credentials_path):
            return False
        try:
            with open(self.credentials_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return bool(data.get("access_token"))
        except Exception:
            return False

    def get_quota_stats(self) -> Dict[str, Any]:
        """Pinterest API rate limits: Standard tier provides 1,000 requests per hour."""
        return {
            "hourly_limit": 1000,
            "period": "1 hour",
            "type": "Pinterest API v5"
        }

    def publish(
        self,
        manifest: AssetManifest,
        script: ScriptPackage,
        dry_run: bool = True,
        privacy: str = "public"
    ) -> PublishResult:
        valid, errors = self.validate(manifest, script)
        if not valid:
            return PublishResult(
                success=False,
                platform=self.platform,
                item_id="",
                canonical_url="",
                dry_run=dry_run,
                error_message="; ".join(errors)
            )

        is_auth = self.is_authenticated()
        effective_dry_run = dry_run or not is_auth

        bundle_dir = os.path.join(EXPORTS_DIR, script.job_id)
        os.makedirs(bundle_dir, exist_ok=True)

        pin_payload = {
            "title": script.title[:100],
            "description": script.description[:500],
            "link": script.sources[0] if script.sources else "https://github.com/gurugangadhar/Munder-Os",
            "board_id": "munder_difflin_ai_tools",
            "media_source": {
                "source_type": "video_id" if manifest.video_path else "image_url"
            },
            "job_id": script.job_id,
            "division_id": script.division_id,
            "created_at": datetime.now().isoformat()
        }

        with open(os.path.join(bundle_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(pin_payload, f, indent=2)

        if manifest.video_path and os.path.exists(manifest.video_path):
            target_mp4 = os.path.join(bundle_dir, os.path.basename(manifest.video_path))
            if not os.path.exists(target_mp4):
                try:
                    shutil.copy2(manifest.video_path, target_mp4)
                except Exception:
                    pass

        if effective_dry_run:
            sim_id = f"pin_{script.job_id[-8:]}"
            return PublishResult(
                success=True,
                platform=self.platform,
                item_id=sim_id,
                canonical_url=f"https://pinterest.com/pin/{sim_id}",
                quota_used=1,
                dry_run=True,
                export_bundle_path=os.path.abspath(bundle_dir),
                metadata=pin_payload
            )

        return PublishResult(
            success=False,
            platform=self.platform,
            item_id="",
            canonical_url="",
            dry_run=False,
            error_message="Live Pinterest publishing requires registered Board ID and developer OAuth token."
        )

    def get_status(self, item_id: str) -> Dict[str, Any]:
        return {
            "item_id": item_id,
            "status": "ready_for_scheduling",
            "type": "Pin"
        }
