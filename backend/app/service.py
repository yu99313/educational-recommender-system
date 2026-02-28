from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List

from .config import CACHE_DIR, MAX_REQUESTION_ROUNDS
from .data_loader import DataLoader, ItemMeta
from .item_builder import ItemBuilder
from .llm_fallback import LLMFallbackRecommender
from .models import SurveyQuestion
from .strategy_judge import StrategyJudge


class RecommendationService:
    def __init__(self, survey_path: Path, train_path: Path):
        self.loader = DataLoader(survey_path=survey_path, train_path=train_path)
        self.all_items: Dict[str, ItemMeta] = {}
        self.short_questions: Dict[str, List[Dict]] = {}
        self.removed_by_subscale: Dict[str, Dict[str, List[str]]] = {}
        self.subscale_map: Dict[str, Dict[str, List[int]]] = {}
        self.train_sheets = {}
        self.judge: StrategyJudge | None = None
        self.llm = LLMFallbackRecommender()
        self._initialize()

    def _initialize(self) -> None:
        all_items, grouped_items, subscale_map = self.loader.build_item_bank()
        self.all_items = all_items
        self.subscale_map = subscale_map
        self.train_sheets = self.loader.load_train_sheets()

        cache_file = CACHE_DIR / "item_builder_results.json"
        if cache_file.exists():
            with cache_file.open("r", encoding="utf-8") as f:
                payload = json.load(f)
        else:
            builder = ItemBuilder(all_items, grouped_items, self.train_sheets)
            payload = builder.build()
            builder.save(cache_file, payload)

        self.short_questions = payload["selected_questions"]
        self.removed_by_subscale = payload["removed_by_subscale"]
        self.judge = StrategyJudge(
            train_sheets=self.train_sheets,
            selected_questions=self.short_questions,
            subscale_map=self.subscale_map,
        )

    def get_short_questions(self) -> List[SurveyQuestion]:
        output: List[SurveyQuestion] = []
        for scale in ("EQ", "FLA"):
            for q in self.short_questions[scale]:
                output.append(
                    SurveyQuestion(
                        question_id=q["question_id"],
                        scale=q["scale"],
                        item_number=int(q["item_number"]),
                        subscale=q["subscale"],
                        text=q["text"],
                        reverse_coded=bool(q.get("reverse_coded", False)),
                    )
                )
        return sorted(output, key=lambda x: (x.scale, x.subscale, x.item_number))

    def recommend(
        self, responses: Dict[str, float], tie_breaker_answers: Dict[str, List[float]] | None
    ) -> Dict:
        if not self.judge:
            raise RuntimeError("Service is not initialized.")
        return self.judge.recommend(responses, tie_breaker_answers)

    def llm_fallback_recommend(
        self,
        responses: Dict[str, float],
        tie_breaker_answers: Dict[str, List[float]] | None,
        user_profile: Dict[str, str] | None,
        force: bool = False,
    ) -> Dict:
        base = self.recommend(responses, tie_breaker_answers)
        if not base["tie_triggered"] and not force:
            return {
                "recommended_strategy": base["recommended_strategy"],
                "reason": "Rule-based result was not tied; LLM fallback skipped.",
                "confidence": 0.9,
                "model": "rule-based",
                "used_llm": False,
                "base_tie_triggered": base["tie_triggered"],
                "base_score_gap": base["score_gap"],
            }
        llm_result = self.llm.decide(base_result=base, user_profile=user_profile)
        return {
            **llm_result,
            "base_tie_triggered": base["tie_triggered"],
            "base_score_gap": base["score_gap"],
        }

    def get_requestion_pair(
        self, eq_subscale: str, fla_subscale: str, used_question_ids: List[str]
    ) -> List[SurveyQuestion]:
        eq_candidates = self._candidate_pool("EQ", eq_subscale, used_question_ids)
        fla_candidates = self._candidate_pool("FLA", fla_subscale, used_question_ids)

        questions = []
        if eq_candidates:
            questions.append(self._to_question(random.choice(eq_candidates)))
        if fla_candidates:
            questions.append(self._to_question(random.choice(fla_candidates)))
        return questions

    def _candidate_pool(self, scale: str, subscale: str, used: List[str]) -> List[str]:
        pools = self.removed_by_subscale.get(scale, {})
        candidates = [qid for qid in pools.get(subscale, []) if qid not in used]
        if candidates:
            return candidates
        return [
            qid
            for arr in pools.values()
            for qid in arr
            if qid not in used
        ]

    def _to_question(self, question_id: str) -> SurveyQuestion:
        item = self.all_items[question_id]
        return SurveyQuestion(
            question_id=item.question_id,
            scale=item.scale,
            item_number=item.item_number,
            subscale=item.subscale,
            text=item.text,
            reverse_coded=item.reverse_coded,
        )

    @property
    def round_limit(self) -> int:
        return MAX_REQUESTION_ROUNDS
