from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import SURVEY_FILE, TRAIN_FILE
from .models import (
    LLMFallbackRequest,
    LLMFallbackResponse,
    QuestionsResponse,
    RecommendRequest,
    RecommendResponse,
    RequestionRequest,
    RequestionResponse,
)
from .service import RecommendationService

app = FastAPI(title="Adaptive Learning Strategy API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = RecommendationService(survey_path=SURVEY_FILE, train_path=TRAIN_FILE)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/questions", response_model=QuestionsResponse)
def questions() -> QuestionsResponse:
    qs = service.get_short_questions()
    return QuestionsResponse(total_questions=len(qs), questions=qs)


@app.post("/api/recommend", response_model=RecommendResponse)
def recommend(payload: RecommendRequest) -> RecommendResponse:
    try:
        result = service.recommend(payload.responses, payload.tie_breaker_answers)
        return RecommendResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/requestion", response_model=RequestionResponse)
def requestion(payload: RequestionRequest) -> RequestionResponse:
    questions = service.get_requestion_pair(
        payload.eq_subscale,
        payload.fla_subscale,
        payload.used_question_ids,
    )
    return RequestionResponse(round_limit=service.round_limit, questions=questions)


@app.post("/api/recommend/llm-fallback", response_model=LLMFallbackResponse)
def recommend_llm_fallback(payload: LLMFallbackRequest) -> LLMFallbackResponse:
    result = service.llm_fallback_recommend(
        responses=payload.responses,
        tie_breaker_answers=payload.tie_breaker_answers,
        user_profile=payload.user_profile,
        force=payload.force,
    )
    return LLMFallbackResponse(**result)
