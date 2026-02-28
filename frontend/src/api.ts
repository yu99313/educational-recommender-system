import type {
  LLMFallbackResponse,
  QuestionsResponse,
  RecommendResponse,
  RequestionResponse
} from "./types";

const API_BASE = "http://localhost:8000/api";

export async function fetchQuestions(): Promise<QuestionsResponse> {
  const res = await fetch(`${API_BASE}/questions`);
  if (!res.ok) throw new Error("질문 목록을 불러오지 못했습니다.");
  return res.json();
}

export async function fetchRecommendation(payload: {
  responses: Record<string, number>;
  tie_breaker_answers?: Record<string, number[]>;
}): Promise<RecommendResponse> {
  const res = await fetch(`${API_BASE}/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error("추천 결과를 불러오지 못했습니다.");
  return res.json();
}

export async function fetchRequestion(payload: {
  eq_subscale: string;
  fla_subscale: string;
  used_question_ids: string[];
}): Promise<RequestionResponse> {
  const res = await fetch(`${API_BASE}/requestion`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error("재질문을 불러오지 못했습니다.");
  return res.json();
}

export async function fetchLLMFallbackRecommendation(payload: {
  responses: Record<string, number>;
  tie_breaker_answers?: Record<string, number[]>;
  user_profile?: Record<string, string>;
  force?: boolean;
}): Promise<LLMFallbackResponse> {
  const res = await fetch(`${API_BASE}/recommend/llm-fallback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error("LLM 보완 추천을 불러오지 못했습니다.");
  return res.json();
}
