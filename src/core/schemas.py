"""Pydantic schemas for the Football Value-Betting Agent.
Adheres to the machine-readable specifications in the plan.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator


class MarketType(str, Enum):
    ONE_X_TWO = "1X2"
    BOTH_TEAMS_TO_SCORE = "BTTS"
    OVER_UNDER_2_5 = "OVER_UNDER_2_5"
    OVER_UNDER_1_5 = "OVER_UNDER_1_5"
    OVER_UNDER_3_5 = "OVER_UNDER_3_5"
    ASIAN_HANDICAP = "ASIAN_HANDICAP"


class SelectionType(str, Enum):
    HOME = "home"
    DRAW = "draw"
    AWAY = "away"
    YES = "yes"
    NO = "no"
    OVER = "over"
    UNDER = "under"


class OddsRecord(BaseModel):
    bookmaker: str
    odds: float = Field(..., gt=1.0, description="Decimal odds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MarketOdds(BaseModel):
    market: MarketType
    odds: Dict[str, float] = Field(..., description="Map of selection to decimal odds")
    bookmaker: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MatchFixture(BaseModel):
    match_id: str
    competition: str
    home_team: str
    away_team: str
    kickoff_time: datetime
    is_completed: bool = False
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    home_npxg: Optional[float] = None
    away_npxg: Optional[float] = None


class FairProbabilities(BaseModel):
    method: str = Field(..., description="Method used, e.g., 'shin', 'power', 'proportional'")
    probabilities: Dict[str, float] = Field(..., description="Map of selection to devigged true probability")

    @field_validator("probabilities")
    @classmethod
    def validate_sum(cls, v: Dict[str, float]) -> Dict[str, float]:
        total = sum(v.values())
        if not (0.98 <= total <= 1.02):
            raise ValueError(f"Probabilities must sum approximately to 1.0, got {total}")
        return v


class AnalyticalMatchProbabilities(BaseModel):
    home_win: float = Field(..., ge=0.0, le=1.0)
    draw: float = Field(..., ge=0.0, le=1.0)
    away_win: float = Field(..., ge=0.0, le=1.0)
    btts_yes: float = Field(..., ge=0.0, le=1.0)
    btts_no: float = Field(..., ge=0.0, le=1.0)
    over_1_5: float = Field(..., ge=0.0, le=1.0)
    under_1_5: float = Field(..., ge=0.0, le=1.0)
    over_2_5: float = Field(..., ge=0.0, le=1.0)
    under_2_5: float = Field(..., ge=0.0, le=1.0)
    over_3_5: float = Field(..., ge=0.0, le=1.0)
    under_3_5: float = Field(..., ge=0.0, le=1.0)
    score_matrix: Optional[List[List[float]]] = None


class BetRecommendation(BaseModel):
    match_id: str
    competition: str
    home_team: str
    away_team: str
    market: MarketType
    selection: str
    model_probability: float = Field(..., ge=0.0, le=1.0)
    offered_odds: float = Field(..., gt=1.0)
    fair_sharp_odds: float = Field(..., gt=1.0)
    edge: float = Field(..., description="(model_prob * offered_odds) - 1")
    stake_fraction: float = Field(..., ge=0.0, le=0.05, description="Fraction of bankroll")
    suggested_stake_amount: Optional[float] = None
    confidence_label: str = Field("medium", pattern="^(low|medium|high)$")
    key_factors: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)


class PlayerInjuryContext(BaseModel):
    team: str
    player: Optional[str] = None
    status: str = Field(..., pattern="^(out|doubtful|suspended|returning|rested|other)$")
    confidence: str = Field(..., pattern="^(confirmed|reported|rumour)$")
    source: str
    source_type: str = Field(..., pattern="^(official|journalist|media|social)$")
    published_at: datetime
    expected_impact: str = Field(..., pattern="^(none|low|medium|high)$")
    reasoning: str

