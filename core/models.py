"""
Munder Difflin — Core Data Models & Schemas
Typed Pydantic models for validation, serialization, and state persistence.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    READY_FOR_PUBLISH = "READY_FOR_PUBLISH"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PlatformType(str, Enum):
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    PINTEREST = "pinterest"
    STOREFRONT = "storefront"
    B2B_CRM = "b2b_crm"


class DivisionPlatform(BaseModel):
    name: PlatformType
    format: str
    category_id: Optional[str] = None
    is_made_for_kids: bool = False


class DivisionProduction(BaseModel):
    aspect_ratio: str
    resolution: List[int] = Field(default_factory=lambda: [1080, 1920])
    tts_voice: Optional[str] = "en-US-ChristopherNeural"
    font_family: str = "Arial"
    primary_color: str = "#00E5FF"
    background_color: str = "#0D1117"


class DivisionSchedule(BaseModel):
    daily_target: int = 1
    max_daily: int = 2
    preferred_hours: List[str] = Field(default_factory=lambda: ["10:00"])


class DivisionConfig(BaseModel):
    id: str
    name: str
    enabled: bool = True
    priority: int = 1
    description: str
    target_audience: str
    platforms: List[DivisionPlatform]
    publishing_schedule: DivisionSchedule
    production: DivisionProduction
    revenue_models: List[str] = Field(default_factory=list)


class Job(BaseModel):
    job_id: str
    division_id: str
    idempotency_key: str
    status: JobStatus = JobStatus.QUEUED
    topic: str
    stage: str = "init"
    retry_count: int = 0
    max_retries: int = 3
    payload: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class TopicCandidate(BaseModel):
    candidate_id: str
    division_id: str
    title: str
    summary: str
    source_url: str
    credibility_score: float = 1.0
    discovered_at: datetime = Field(default_factory=datetime.now)
    used_in_job_id: Optional[str] = None


class ScriptPackage(BaseModel):
    job_id: str
    division_id: str
    title: str
    hook: str
    voiceover_lines: List[str]
    call_to_action: str
    description: str
    tags: List[str] = Field(default_factory=list)
    estimated_duration_seconds: int = 50
    sources: List[str] = Field(default_factory=list)


class AssetManifest(BaseModel):
    job_id: str
    division_id: str
    audio_path: Optional[str] = None
    subtitles_path: Optional[str] = None
    video_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    extra_files: List[str] = Field(default_factory=list)
    file_sizes_bytes: Dict[str, int] = Field(default_factory=dict)
    render_duration_seconds: float = 0.0
    qa_passed: bool = False
    qa_notes: List[str] = Field(default_factory=list)


class PublicationRecord(BaseModel):
    publication_id: str
    job_id: str
    division_id: str
    platform: PlatformType
    platform_item_id: str
    canonical_url: str
    published_at: datetime = Field(default_factory=datetime.now)
    privacy_status: str = "public"


class FinancialEntry(BaseModel):
    entry_id: str
    division_id: str
    type: str  # "REVENUE" or "EXPENSE"
    amount_inr: float = 0.0
    category: str
    description: str
    job_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class SystemHealthReport(BaseModel):
    status: str = "HEALTHY"
    timestamp: datetime = Field(default_factory=datetime.now)
    disk_free_gb: float
    active_jobs_count: int
    pending_approvals_count: int
    failed_jobs_count: int
    emergency_stop_active: bool
    issues: List[str] = Field(default_factory=list)
