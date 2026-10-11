"""
Munder Difflin — Base Publishing Definitions & Results
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
from core.models import PlatformType, AssetManifest, ScriptPackage


class PublishResult(BaseModel):
    success: bool
    platform: PlatformType
    item_id: str
    canonical_url: str
    quota_used: int = 0
    dry_run: bool = True
    error_message: Optional[str] = None
    published_at: datetime = Field(default_factory=datetime.now)
    export_bundle_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BasePublisher(ABC):
    """Abstract publisher interface for official social media and distribution channels."""

    def __init__(self, platform: PlatformType):
        self.platform = platform

    @abstractmethod
    def validate(self, manifest: AssetManifest, script: ScriptPackage) -> Tuple[bool, List[str]]:
        """Validates assets and script metadata before publication attempt."""
        pass

    @abstractmethod
    def publish(
        self,
        manifest: AssetManifest,
        script: ScriptPackage,
        dry_run: bool = True,
        privacy: str = "public"
    ) -> PublishResult:
        """Publishes the content or exports an upload-ready package if in dry-run mode."""
        pass

    @abstractmethod
    def get_status(self, item_id: str) -> Dict[str, Any]:
        """Retrieves live publication or processing status from platform API."""
        pass

    @abstractmethod
    def get_quota_stats(self) -> Dict[str, Any]:
        """Returns daily API quota usage and limits."""
        pass
