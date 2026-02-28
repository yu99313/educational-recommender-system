from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SurveyQuestion(BaseModel):
    question_id: str
    scale: str
    item_number: int
    subscale: str
    text: str
    reverse_coded: bool = False
    likert_min: int = 1
    likert_max: int = 5


class QuestionsResponse(BaseModel):
    total_questions: int
    questions: List[SurveyQuestion]


class RecommendRequest(BaseModel):
    responses: Dict[str, float] = Field(
        ..., description="Key: question_id (EQ-7), Value: 1~5"
    )
    tie_breaker_answers: Optional[Dict[str, List[float]]] = None


class StrategyCandidate(BaseModel):
    driver: str
    driver_subscale: str
    strategy_subscale: str
    correlation: float
    user_subscale_score: float
    final_score: float


class RecommendResponse(BaseModel):
    recommended_strategy: str
    tie_triggered: bool
    score_gap: float
    summary: str
    candidates: List[StrategyCandidate]
    top_eq_subscale: str
    top_fla_subscale: str
    eq_scores: Dict[str, float]
    fla_scores: Dict[str, float]
    strategy_ranking: List[Dict[str, float | str]]


class RequestionRequest(BaseModel):
    eq_subscale: str
    fla_subscale: str
    used_question_ids: List[str] = []


class RequestionResponse(BaseModel):
    round_limit: int
    questions: List[SurveyQuestion]


class LLMFallbackRequest(BaseModel):
    responses: Dict[str, float]
    tie_breaker_answers: Optional[Dict[str, List[float]]] = None
    user_profile: Optional[Dict[str, str]] = None
    force: bool = False


class LLMFallbackResponse(BaseModel):
    recommended_strategy: str
    reason: str
    confidence: float
    model: str
    used_llm: bool
    base_tie_triggered: bool
    base_score_gap: float
