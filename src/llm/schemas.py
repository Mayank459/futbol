"""Pydantic schemas for LLM Agent extraction and explanation.
Strictly adheres to Section 14 of the specification.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class PlayerStatus(str, Enum):
    OUT = "out"
    DOUBTFUL = "doubtful"
    SUSPENDED = "suspended"
    RETURNING = "returning"
    RESTED = "rested"
    OTHER = "other"


class InformationConfidence(str, Enum):
    CONFIRMED = "confirmed"
    REPORTED = "reported"
    RUMOUR = "rumour"


class SourceType(str, Enum):
    OFFICIAL = "official"
    JOURNALIST = "journalist"
    MEDIA = "media"
    SOCIAL = "social"


class ImpactLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TeamNewsItem(BaseModel):
    team: str = Field(..., description="Team name")
    player: Optional[str] = Field(None, description="Player name, or null if general squad news")
    status: PlayerStatus
    confidence: InformationConfidence
    source: str = Field(..., description="Name of newspaper, club channel, or journalist")
    source_type: SourceType
    published_at: Optional[str] = Field(None, description="Publication ISO timestamp if known")
    expected_impact: ImpactLevel
    reasoning: str = Field(..., description="Reasoning based strictly on provided text")


class NewsExtractionBatch(BaseModel):
    items: List[TeamNewsItem] = Field(default_factory=list)


class RotationEstimate(BaseModel):
    match_id: str
    team: str
    expected_changes: float = Field(..., ge=0.0, le=11.0, description="Estimated number of rotated starters")
    probability_heavy_rotation: float = Field(..., ge=0.0, le=1.0, description="Probability team rotates >= 4 starters")
    evidence: List[str] = Field(default_factory=list, description="Direct quotes or fixture congestion facts")


class PickExplanation(BaseModel):
    match_id: str
    selection: str
    headline_reason: str
    statistical_context: str
    qualitative_context: str
    main_risks: List[str]

