from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from .config import MIN_CRONBACH_ALPHA, SIMILARITY_THRESHOLD, TARGET_SHORT_ITEMS
from .data_loader import ItemMeta


def cronbach_alpha(df: pd.DataFrame) -> float:
    if df.shape[1] < 2:
        return 0.0
    item_vars = df.var(axis=0, ddof=1)
    total = df.sum(axis=1)
    total_var = total.var(ddof=1)
    if total_var == 0 or np.isnan(total_var):
        return 0.0
    k = df.shape[1]
    alpha = (k / (k - 1)) * (1 - item_vars.sum() / total_var)
    return float(alpha)


class ItemBuilder:
    def __init__(
        self,
        all_items: Dict[str, ItemMeta],
        grouped_items: Dict[str, List[ItemMeta]],
        train_sheets: Dict[str, pd.DataFrame],
    ):
        self.all_items = all_items
        self.grouped_items = grouped_items
        self.train_sheets = train_sheets

    def build(self) -> Dict:
        selected_by_scale: Dict[str, List[ItemMeta]] = {}
        removed_by_subscale: Dict[str, Dict[str, List[str]]] = {"EQ": {}, "FLA": {}}
        alpha_report: Dict[str, float] = {}

        for scale in ("EQ", "FLA"):
            items = self.grouped_items[scale]
            target_total = TARGET_SHORT_ITEMS[scale]
            groups = self._group_by_subscale(items)
            quotas = self._allocate_quotas(groups, target_total)

            selected: List[ItemMeta] = []
            for subscale, sub_items in groups.items():
                quota = quotas[subscale]
                sub_selected = self._select_diverse(sub_items, quota)
                selected.extend(sub_selected)
                selected_ids = {q.question_id for q in sub_selected}
                removed_by_subscale[scale][subscale] = [
                    q.question_id for q in sub_items if q.question_id not in selected_ids
                ]

            selected = self._enforce_target_count(selected, groups, target_total)
            alpha_report[scale] = self._compute_alpha(scale, selected)
            if alpha_report[scale] < MIN_CRONBACH_ALPHA:
                selected = self._repair_alpha(scale, selected, groups, target_total)
                alpha_report[scale] = self._compute_alpha(scale, selected)

            selected_by_scale[scale] = selected

        payload = {
            "selected_questions": {
                scale: [self._to_public_dict(item) for item in items]
                for scale, items in selected_by_scale.items()
            },
            "removed_by_subscale": removed_by_subscale,
            "alpha_report": alpha_report,
        }
        return payload

    def save(self, output_path: Path, payload: Dict) -> None:
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def _group_by_subscale(self, items: List[ItemMeta]) -> Dict[str, List[ItemMeta]]:
        groups: Dict[str, List[ItemMeta]] = defaultdict(list)
        for item in items:
            groups[item.subscale].append(item)
        return dict(groups)

    def _allocate_quotas(self, groups: Dict[str, List[ItemMeta]], target: int) -> Dict[str, int]:
        total = sum(len(v) for v in groups.values())
        quotas = {}
        for sub, arr in groups.items():
            ratio = len(arr) / total if total else 0
            quotas[sub] = max(1, int(round(ratio * target)))
            quotas[sub] = min(quotas[sub], len(arr))

        current = sum(quotas.values())
        keys = sorted(groups.keys(), key=lambda k: len(groups[k]), reverse=True)
        while current < target:
            for key in keys:
                if quotas[key] < len(groups[key]):
                    quotas[key] += 1
                    current += 1
                    if current == target:
                        break
        while current > target:
            for key in reversed(keys):
                if quotas[key] > 1:
                    quotas[key] -= 1
                    current -= 1
                    if current == target:
                        break
        return quotas

    def _select_diverse(self, items: List[ItemMeta], quota: int) -> List[ItemMeta]:
        if len(items) <= quota:
            return list(items)

        embeddings = self._encode([item.text for item in items])
        sim = cosine_similarity(embeddings)
        selected_idx: List[int] = []

        for idx in range(len(items)):
            if len(selected_idx) >= quota:
                break
            if not selected_idx:
                selected_idx.append(idx)
                continue
            max_sim = max(sim[idx, j] for j in selected_idx)
            if max_sim < SIMILARITY_THRESHOLD:
                selected_idx.append(idx)

        if len(selected_idx) < quota:
            remaining = [i for i in range(len(items)) if i not in selected_idx]
            diversity_scores = []
            for i in remaining:
                if not selected_idx:
                    score = 1.0
                else:
                    score = min(1 - sim[i, j] for j in selected_idx)
                diversity_scores.append((score, i))
            diversity_scores.sort(reverse=True)
            selected_idx.extend([idx for _, idx in diversity_scores[: quota - len(selected_idx)]])

        selected_idx = sorted(selected_idx[:quota])
        return [items[i] for i in selected_idx]

    def _enforce_target_count(
        self,
        selected: List[ItemMeta],
        groups: Dict[str, List[ItemMeta]],
        target: int,
    ) -> List[ItemMeta]:
        selected_ids = {item.question_id for item in selected}
        if len(selected) == target:
            return selected

        if len(selected) < target:
            candidates = [
                item
                for group in groups.values()
                for item in group
                if item.question_id not in selected_ids
            ]
            selected.extend(candidates[: target - len(selected)])
            return selected[:target]

        # len(selected) > target
        return selected[:target]

    def _compute_alpha(self, scale: str, selected: List[ItemMeta]) -> float:
        data = self.train_sheets[scale]
        item_cols = [item.item_number for item in selected if item.item_number in data.columns]
        if len(item_cols) < 2:
            return 0.0
        working = data[item_cols].dropna().copy()
        reverse_cols = [item.item_number for item in selected if item.reverse_coded]
        for col in reverse_cols:
            if col in working.columns:
                working[col] = 6 - working[col]
        return cronbach_alpha(working)

    def _repair_alpha(
        self,
        scale: str,
        selected: List[ItemMeta],
        groups: Dict[str, List[ItemMeta]],
        target: int,
    ) -> List[ItemMeta]:
        selected_ids = {s.question_id for s in selected}
        candidates = [
            item for arr in groups.values() for item in arr if item.question_id not in selected_ids
        ]
        candidates.sort(key=lambda x: x.item_number)

        best = list(selected)
        best_alpha = self._compute_alpha(scale, best)
        for candidate in candidates:
            trial = list(best)
            if len(trial) >= target:
                trial[-1] = candidate
            else:
                trial.append(candidate)
            alpha = self._compute_alpha(scale, trial)
            if alpha > best_alpha:
                best = trial
                best_alpha = alpha
            if best_alpha >= MIN_CRONBACH_ALPHA:
                break
        return best[:target]

    def _encode(self, texts: List[str]) -> np.ndarray:
        from sklearn.feature_extraction.text import TfidfVectorizer

        vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        matrix = vectorizer.fit_transform(texts)
        return matrix.toarray()

    def _to_public_dict(self, item: ItemMeta) -> Dict:
        d = asdict(item)
        d["question_id"] = item.question_id
        return d
