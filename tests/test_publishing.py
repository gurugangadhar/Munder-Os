"""
Munder Difflin — Platform Publishing & Distribution Test Suite
Tests pre-flight compliance, dry-run exports, idempotency, and quota tracking.
"""

import os
import shutil
import unittest
from datetime import datetime
from core.models import PlatformType, AssetManifest, ScriptPackage
from core.database import Database
from core.publishing.validator import PreflightValidator
from core.publishing.youtube import YouTubePublisher
from core.publishing.instagram import InstagramPublisher
from core.publishing.pinterest import PinterestPublisher
from core.publishing.manager import PublishingManager


TEST_DB_PATH = "data/test_publishing.db"


class TestPublishingPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        cls.db = Database(TEST_DB_PATH)
        cls.manager = PublishingManager(db=cls.db)

        # Insert prerequisite division and job into test db for FK constraints
        with cls.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR IGNORE INTO divisions (id, name, enabled, priority, config_json, updated_at)
            VALUES ('div_a_tech', 'AI Tech Media', 1, 1, '{}', '2026-10-11T00:00:00');
            """)
            cursor.execute("""
            INSERT OR IGNORE INTO jobs (job_id, division_id, idempotency_key, status, topic, stage, retry_count, max_retries, payload_json, created_at, updated_at)
            VALUES ('job_idempotent_01', 'div_a_tech', 'key_test_01', 'COMPLETED', 'Idempotency Test Video', 'qa', 0, 3, '{}', '2026-10-11T00:00:00', '2026-10-11T00:00:00');
            """)

        # Create dummy test MP4
        os.makedirs("data/test_assets", exist_ok=True)
        cls.test_video_path = "data/test_assets/test_short.mp4"
        with open(cls.test_video_path, "wb") as f:
            f.write(b"\x00" * 4096)  # 4KB mock MP4

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        if os.path.exists("data/test_assets"):
            shutil.rmtree("data/test_assets", ignore_errors=True)
        if os.path.exists("data/exports"):
            shutil.rmtree("data/exports", ignore_errors=True)

    def test_01_youtube_preflight_validation(self):
        valid_script = ScriptPackage(
            job_id="job_yt_01",
            division_id="div_a_tech",
            title="3 Free AI Coding Agents You Can Run Locally",
            hook="Stop paying for AI.",
            voiceover_lines=["Point 1", "Point 2"],
            call_to_action="Comment below.",
            description="Detailed review of local agents.",
            tags=["AI", "Python", "LocalLLM"],
            estimated_duration_seconds=50,
            sources=["https://ollama.com"]
        )
        valid_manifest = AssetManifest(
            job_id="job_yt_01",
            division_id="div_a_tech",
            video_path=self.test_video_path,
            qa_passed=True
        )

        ok, errors = PreflightValidator.validate_youtube_shorts(valid_manifest, valid_script)
        self.assertTrue(ok, f"Validation failed with: {errors}")

        # Test duration boundary (> 60s should fail)
        invalid_script = valid_script.model_copy(update={"estimated_duration_seconds": 65})
        ok, errors = PreflightValidator.validate_youtube_shorts(valid_manifest, invalid_script)
        self.assertFalse(ok)
        self.assertTrue(any("60s" in e for e in errors))

        # Test QA gate failure
        unapproved_manifest = valid_manifest.model_copy(update={"qa_passed": False})
        ok, errors = PreflightValidator.validate_youtube_shorts(unapproved_manifest, valid_script)
        self.assertFalse(ok)
        self.assertTrue(any("QA audit" in e for e in errors))

    def test_02_youtube_dry_run_export(self):
        publisher = YouTubePublisher()
        script = ScriptPackage(
            job_id="job_yt_export",
            division_id="div_a_tech",
            title="Automate Boring Tasks with Python",
            hook="Save hours every day.",
            voiceover_lines=["Intro"],
            call_to_action="Follow for more.",
            description="Python automation workflows.",
            tags=["Python", "Automation"],
            estimated_duration_seconds=45,
            sources=["https://python.org"]
        )
        manifest = AssetManifest(
            job_id="job_yt_export",
            division_id="div_a_tech",
            video_path=self.test_video_path,
            qa_passed=True
        )

        res = publisher.publish(manifest, script, dry_run=True, privacy="unlisted")
        self.assertTrue(res.success)
        self.assertTrue(res.dry_run)
        self.assertTrue(res.canonical_url.startswith("https://youtube.com/shorts/"))
        self.assertIsNotNone(res.export_bundle_path)
        self.assertTrue(os.path.exists(os.path.join(res.export_bundle_path, "metadata.json")))
        self.assertTrue(os.path.exists(os.path.join(res.export_bundle_path, "description.txt")))

    def test_03_publishing_manager_idempotency(self):
        script = ScriptPackage(
            job_id="job_idempotent_01",
            division_id="div_a_tech",
            title="Idempotency Test Video",
            hook="Testing publishing.",
            voiceover_lines=["Test"],
            call_to_action="Subscribe.",
            description="Testing idempotent database writes.",
            tags=["Test"],
            estimated_duration_seconds=30,
            sources=["https://test.local"]
        )
        manifest = AssetManifest(
            job_id="job_idempotent_01",
            division_id="div_a_tech",
            video_path=self.test_video_path,
            qa_passed=True
        )

        # First publication attempt
        res1 = self.manager.publish_asset(manifest, script, PlatformType.YOUTUBE, dry_run=True)
        self.assertTrue(res1.success)

        # Second publication attempt (Should be caught by idempotency)
        res2 = self.manager.publish_asset(manifest, script, PlatformType.YOUTUBE, dry_run=True)
        self.assertTrue(res2.success)
        self.assertTrue(res2.metadata.get("duplicate_prevented", False))
        self.assertEqual(res1.canonical_url, res2.canonical_url)

        # Verify exactly one record in database
        publications = self.manager.list_publications()
        matching = [p for p in publications if p["job_id"] == "job_idempotent_01"]
        self.assertEqual(len(matching), 1)

    def test_04_quota_tracking(self):
        pub = YouTubePublisher()
        stats = pub.get_quota_stats()
        self.assertEqual(stats["limit"], 10000)
        self.assertGreaterEqual(stats["remaining"], 0)
        self.assertIn("max_uploads_remaining", stats)

    def test_05_platform_readiness(self):
        readiness = self.manager.get_platform_readiness()
        self.assertIn("youtube", readiness)
        self.assertIn("instagram", readiness)
        self.assertIn("pinterest", readiness)
        self.assertEqual(readiness["youtube"]["mode"], "Dry-Run / Manual Export Ready")


if __name__ == "__main__":
    unittest.main()
