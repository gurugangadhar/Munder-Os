"""
Munder Difflin — Multi-Platform Publishing & Distribution Engine
Handles validation, pre-flight checks, OAuth flows, resumable video uploads,
dry-run asset exports, and publication audit tracking across YouTube, Instagram, and Pinterest.
"""

from core.publishing.base import BasePublisher, PublishResult
from core.publishing.validator import PreflightValidator
from core.publishing.youtube import YouTubePublisher
from core.publishing.instagram import InstagramPublisher
from core.publishing.pinterest import PinterestPublisher
from core.publishing.manager import PublishingManager

__all__ = [
    "BasePublisher",
    "PublishResult",
    "PreflightValidator",
    "YouTubePublisher",
    "InstagramPublisher",
    "PinterestPublisher",
    "PublishingManager",
]
