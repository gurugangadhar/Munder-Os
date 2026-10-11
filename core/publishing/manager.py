"""
Munder Difflin — Central Publishing & Distribution Manager
Coordinates multi-platform dispatch, idempotency publication logging,
dry-run asset exports, and quota audit reporting.
"""

import os
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from core.models import PlatformType, AssetManifest, ScriptPackage, PublicationRecord
from core.database import Database
from core.publishing.base import BasePublisher, PublishResult
from core.publishing.youtube import YouTubePublisher
from core.publishing.instagram import InstagramPublisher
from core.publishing.pinterest import PinterestPublisher


class PublishingManager:
    """Master controller for all authorized publication channels."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()
        self.publishers: Dict[PlatformType, BasePublisher] = {
            PlatformType.YOUTUBE: YouTubePublisher(),
            PlatformType.INSTAGRAM: InstagramPublisher(),
            PlatformType.PINTEREST: PinterestPublisher(),
        }

    def get_publisher(self, platform: PlatformType) -> Optional[BasePublisher]:
        return self.publishers.get(platform)

    def is_already_published(self, job_id: str, platform: PlatformType) -> Optional[Dict[str, Any]]:
        """Idempotency check: Verifies if asset has already been recorded on this platform."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM publications WHERE job_id = ? AND platform = ?;
            """, (job_id, platform.value))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_platform_readiness(self) -> Dict[str, Any]:
        """Returns connection and quota status for all platforms."""
        readiness = {}
        for plat, pub in self.publishers.items():
            is_auth = pub.is_authenticated()
            quota = pub.get_quota_stats()
            readiness[plat.value] = {
                "name": plat.value.title(),
                "authenticated": is_auth,
                "mode": "Live API" if is_auth else "Dry-Run / Manual Export Ready",
                "quota": quota
            }
        return readiness

    def list_publications(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves history of official publications from database."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM publications ORDER BY published_at DESC LIMIT ?;
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def publish_asset(
        self,
        manifest: AssetManifest,
        script: ScriptPackage,
        platform: PlatformType = PlatformType.YOUTUBE,
        dry_run: bool = True,
        privacy: str = "private"
    ) -> PublishResult:
        """
        Validates, executes, and records publication for a produced asset.
        Enforces idempotency to prevent duplicate publications.
        """
        # 1. Idempotency Check
        existing = self.is_already_published(manifest.job_id, platform)
        if existing:
            return PublishResult(
                success=True,
                platform=platform,
                item_id=existing["platform_item_id"],
                canonical_url=existing["canonical_url"],
                dry_run=False,
                error_message="Asset previously published (Idempotency matched).",
                metadata={"duplicate_prevented": True, "existing_record": existing}
            )

        # 2. Select Publisher
        publisher = self.get_publisher(platform)
        if not publisher:
            return PublishResult(
                success=False,
                platform=platform,
                item_id="",
                canonical_url="",
                dry_run=dry_run,
                error_message=f"Publisher for platform '{platform.value}' not registered."
            )

        # 3. Execute Publish (or Dry-Run Export)
        result = publisher.publish(manifest, script, dry_run=dry_run, privacy=privacy)

        # 4. Record to Database if Successful
        if result.success:
            pub_id = f"pub_{uuid.uuid4().hex[:12]}"
            now_iso = datetime.now().isoformat()
            with self.db.transaction() as conn:
                cursor = conn.cursor()
                # Ensure referenced job exists to satisfy foreign key
                cursor.execute("SELECT job_id FROM jobs WHERE job_id = ?;", (manifest.job_id,))
                if not cursor.fetchone():
                    cursor.execute("""
                    INSERT OR IGNORE INTO jobs (
                        job_id, division_id, idempotency_key, status, topic, stage,
                        retry_count, max_retries, payload_json, created_at, updated_at, completed_at
                    ) VALUES (?, ?, ?, 'COMPLETED', ?, 'published', 0, 3, '{}', ?, ?, ?);
                    """, (
                        manifest.job_id,
                        manifest.division_id,
                        f"key_{manifest.job_id}",
                        script.title,
                        now_iso,
                        now_iso,
                        now_iso
                    ))

                cursor.execute("""
                INSERT INTO publications (
                    publication_id, job_id, division_id, platform,
                    platform_item_id, canonical_url, published_at, privacy_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    pub_id,
                    manifest.job_id,
                    manifest.division_id,
                    platform.value,
                    result.item_id,
                    result.canonical_url,
                    result.published_at.isoformat(),
                    privacy
                ))

        return result
