from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

from .config import TIE_GAP_THRESHOLD


@dataclass
class CorrelationChoice:
    driver: str
    driver_subscale: str
    strategy_subscale: str
    correlation: float


class StrategyJudge:
    def __init__(
        self,
        train_sheets: Dict[str, pd.DataFrame],
        selected_questions: Dict[str, List[Dict]],
        subscale_map: Dict[str, Dict[str, List[int]]],
    ):
        self.train = train_sheets
        self.selected = selected_questions
        self.subscale_map = subscale_map
        self.corr_table = self._build_correlation_table()

    def _build_correlation_table(self) -> Dict[str, Dict[str, CorrelationChoice]]:
        eq_scores = self._participant_scores("EQ")
        fla_scores = self._participant_scores("FLA")
        strategy_scores = self._strategy_scores()

        corr_table: Dict[str, Dict[str, CorrelationChoice]] = {"EQ": {}, "FLA": {}}
        for driver, df in (("EQ", eq_scores), ("FLA", fla_scores)):
            for sub in df.columns:
                best = None
                for strategy_sub in strategy_scores.columns:
                    merged = pd.concat([df[sub], strategy_scores[strategy_sub]], axis=1).dropna()
                    if len(merged) < 3:
                        continue
                    corr, _ = pearsonr(merged.iloc[:, 0], merged.iloc[:, 1])
                    if np.isnan(corr):
                        continue
                    if best is None or corr > best.correlation:
                        best = CorrelationChoice(
                            driver=driver,
                            driver_subscale=sub,
                            strategy_subscale=strategy_sub,
                            correlation=float(corr),
                        )
                if best:
                    corr_table[driver][sub] = best

        return corr_table

    def _participant_scores(self, scale: str) -> pd.DataFrame:
        source = self.train[scale].copy()
        if "참여자" in source.columns:
            source = source.set_index("참여자")

        selected_nums = {
            int(q["item_number"]) for q in self.selected[scale] if "item_number" in q
        }
        selected_by_sub = {}
        for subscale, nums in self.subscale_map[scale].items():
            valid = [n for n in nums if n in selected_nums and n in source.columns]
            if valid:
                selected_by_sub[subscale] = valid

        result = {}
        reverse_lookup = {
            int(q["item_number"]): bool(q.get("reverse_coded", False)) for q in self.selected[scale]
        }
        for subscale, items in selected_by_sub.items():
            frame = source[items].copy()
            for col in items:
                if reverse_lookup.get(col):
                    frame[col] = 6 - frame[col]
            result[subscale] = frame.mean(axis=1)
        return pd.DataFrame(result)

    def _strategy_scores(self) -> pd.DataFrame:
        source = self.train["Strategy"].copy()
        if "참여자" in source.columns:
            source = source.set_index("참여자")
        result = {}
        for subscale, nums in self.subscale_map["Strategy"].items():
            valid = [n for n in nums if n in source.columns]
            if valid:
                result[subscale] = source[valid].mean(axis=1)
        return pd.DataFrame(result)

    def recommend(
        self, responses: Dict[str, float], tie_breaker_answers: Dict[str, List[float]] | None = None
    ) -> Dict:
        user_scores = self._user_subscale_scores(responses)
        top_eq = max(user_scores["EQ"].items(), key=lambda x: x[1])[0]
        top_fla = max(user_scores["FLA"].items(), key=lambda x: x[1])[0]

        eq_choice = self.corr_table["EQ"][top_eq]
        fla_choice = self.corr_table["FLA"][top_fla]

        eq_bonus, fla_bonus = self._tie_break_bonus(tie_breaker_answers)
        eq_final = eq_choice.correlation + eq_bonus
        fla_final = fla_choice.correlation + fla_bonus

        score_gap = abs(eq_final - fla_final)
        user_score_gap = abs(user_scores["EQ"][top_eq] - user_scores["FLA"][top_fla])
        winner = eq_choice if eq_final >= fla_final else fla_choice
        # README의 상관계수 박빙 조건을 우선 적용하고,
        # 실제 응답이 박빙인 경우도 재질문으로 보내 정밀도를 확보한다.
        tie_triggered = (score_gap < TIE_GAP_THRESHOLD) or (
            user_score_gap < TIE_GAP_THRESHOLD
        )

        candidates = [
            {
                "driver": "EQ",
                "driver_subscale": top_eq,
                "strategy_subscale": eq_choice.strategy_subscale,
                "correlation": eq_choice.correlation,
                "user_subscale_score": user_scores["EQ"][top_eq],
                "final_score": eq_final,
            },
            {
                "driver": "FLA",
                "driver_subscale": top_fla,
                "strategy_subscale": fla_choice.strategy_subscale,
                "correlation": fla_choice.correlation,
                "user_subscale_score": user_scores["FLA"][top_fla],
                "final_score": fla_final,
            },
        ]
        strategy_ranking = sorted(
            [
                {"strategy_subscale": c["strategy_subscale"], "score": c["final_score"]}
                for c in candidates
            ],
            key=lambda x: x["score"],
            reverse=True,
        )

        return {
            "recommended_strategy": winner.strategy_subscale,
            "tie_triggered": tie_triggered,
            "score_gap": score_gap,
            "summary": f"{winner.driver_subscale} 기반 추천: {winner.strategy_subscale}",
            "candidates": candidates,
            "top_eq_subscale": top_eq,
            "top_fla_subscale": top_fla,
            "eq_scores": user_scores["EQ"],
            "fla_scores": user_scores["FLA"],
            "strategy_ranking": strategy_ranking,
        }

    def _user_subscale_scores(self, responses: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        scores = {"EQ": {}, "FLA": {}}
        for scale in ("EQ", "FLA"):
            selected_by_sub = {}
            for q in self.selected[scale]:
                sub = q["subscale"]
                qid = q["question_id"]
                if qid not in responses:
                    continue
                raw = float(responses[qid])
                score = 6 - raw if q.get("reverse_coded", False) else raw
                selected_by_sub.setdefault(sub, []).append(score)
            for subscale, values in selected_by_sub.items():
                scores[scale][subscale] = float(np.mean(values))

        if not scores["EQ"] or not scores["FLA"]:
            raise ValueError("Responses must include both EQ and FLA short-form items.")
        return scores

    def _tie_break_bonus(self, answers: Dict[str, List[float]] | None) -> Tuple[float, float]:
        if not answers:
            return 0.0, 0.0

        def normalize(vals: List[float]) -> float:
            if not vals:
                return 0.0
            v = np.mean(vals)
            return float((v - 3.0) / 2.0 * 0.05)

        return normalize(answers.get("EQ", [])), normalize(answers.get("FLA", []))
