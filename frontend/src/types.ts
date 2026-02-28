export type Scale = "EQ" | "FLA";

export interface SurveyQuestion {
  question_id: string;
  scale: Scale;
  item_number: number;
  subscale: string;
  text: string;
  reverse_coded: boolean;
  likert_min: number;
  likert_max: number;
}

export interface QuestionsResponse {
  total_questions: number;
  questions: SurveyQuestion[];
}

export interface StrategyCandidate {
  driver: Scale;
  driver_subscale: string;
  strategy_subscale: string;
  correlation: number;
  user_subscale_score: number;
  final_score: number;
}

export interface RecommendResponse {
  recommended_strategy: string;
  tie_triggered: boolean;
  score_gap: number;
  summary: string;
  candidates: StrategyCandidate[];
  top_eq_subscale: string;
  top_fla_subscale: string;
  eq_scores: Record<string, number>;
  fla_scores: Record<string, number>;
  strategy_ranking: { strategy_subscale: string; score: number }[];
}

export interface RequestionResponse {
  round_limit: number;
  questions: SurveyQuestion[];
}

export interface LLMFallbackResponse {
  recommended_strategy: string;
  reason: string;
  confidence: number;
  model: string;
  used_llm: boolean;
  base_tie_triggered: boolean;
  base_score_gap: number;
}
