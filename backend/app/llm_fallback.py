from __future__ import annotations

import json
import os
import sys
from typing import Dict, List, Optional

from .config import PROJECT_ROOT

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


def _load_api_env() -> None:
    env_path = PROJECT_ROOT / "API" / "api.env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


class LLMFallbackRecommender:
    def __init__(self) -> None:
        _load_api_env()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.gpt_api = self._build_client()

    def _build_client(self):
        try:
            from API.GptAPI import GptAPI

            return GptAPI(model=self.model, temperature=0.2, max_tokens=300)
        except Exception:
            return None

    def decide(
        self,
        base_result: Dict,
        user_profile: Optional[Dict[str, str]] = None,
    ) -> Dict:
        candidates: List[Dict] = base_result.get("candidates", [])
        strategy_pool = sorted({c["strategy_subscale"] for c in candidates})

        if not self.gpt_api:
            return self._rule_fallback(base_result, reason_prefix="LLM client unavailable")

        try:
            system = (
                "You are an educational strategy recommender. "
                "Given two candidate strategies and user signal, choose one final strategy. "
                "Return strict JSON only."
            )
            user_prompt = json.dumps(
                {
                    "instruction": "Pick one strategy from strategy_pool.",
                    "strategy_pool": strategy_pool,
                    "base_result": base_result,
                    "user_profile": user_profile or {},
                    "output_schema": {
                        "recommended_strategy": "string",
                        "reason": "string",
                        "confidence": "number between 0 and 1",
                    },
                },
                ensure_ascii=False,
            )
            content = self.gpt_api.chat(system=system, user=user_prompt)
            if not content:
                return self._rule_fallback(base_result, reason_prefix="LLM returned empty response")
            content = content.strip()
            parsed = self._parse_json(content)
            strategy = parsed.get("recommended_strategy", "")
            if strategy not in strategy_pool:
                return self._rule_fallback(base_result, reason_prefix="LLM returned invalid strategy")
            confidence = float(parsed.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))
            return {
                "recommended_strategy": strategy,
                "reason": str(parsed.get("reason", "LLM fallback decision")),
                "confidence": confidence,
                "model": self.model,
                "used_llm": True,
            }
        except Exception:
            return self._rule_fallback(base_result, reason_prefix="LLM request failed")

    def _parse_json(self, text: str) -> Dict:
        try:
            return json.loads(text)
        except Exception:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                return json.loads(text[start : end + 1])
            raise

    def _rule_fallback(self, base_result: Dict, reason_prefix: str) -> Dict:
        candidates: List[Dict] = base_result.get("candidates", [])
        if not candidates:
            return {
                "recommended_strategy": base_result.get("recommended_strategy", "인지전략"),
                "reason": f"{reason_prefix}: no candidates",
                "confidence": 0.3,
                "model": "rule-based",
                "used_llm": False,
            }
        best = max(candidates, key=lambda x: x.get("final_score", 0.0))
        return {
            "recommended_strategy": best["strategy_subscale"],
            "reason": f"{reason_prefix}: choose higher final_score",
            "confidence": 0.55,
            "model": "rule-based",
            "used_llm": False,
        }
