from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pandas as pd

from .config import SUBSCALE_FILE_CANDIDATES


@dataclass
class ItemMeta:
    scale: str
    item_number: int
    subscale: str
    text: str
    reverse_coded: bool = False

    @property
    def question_id(self) -> str:
        return f"{self.scale}-{self.item_number}"


class DataLoader:
    def __init__(self, survey_path: Path, train_path: Path):
        self.survey_path = survey_path
        self.train_path = train_path
        self.subscale_path = self._resolve_subscale_path()

    def _resolve_subscale_path(self) -> Path:
        for candidate in SUBSCALE_FILE_CANDIDATES:
            if candidate.exists():
                return candidate
        names = ", ".join(p.name for p in SUBSCALE_FILE_CANDIDATES)
        raise FileNotFoundError(f"Could not find subscale file among: {names}")

    def load_survey_sheets(self) -> Dict[str, pd.DataFrame]:
        survey_raw = pd.read_excel(self.survey_path, sheet_name=None)
        return {
            "EQ": survey_raw.get("EQ", pd.DataFrame()),
            "FLA": survey_raw.get("Anxiety", survey_raw.get("FLA", pd.DataFrame())),
            "Strategy": survey_raw.get("Strategy", pd.DataFrame()),
        }

    def load_subscale_sheets(self) -> Dict[str, pd.DataFrame]:
        subscale_raw = pd.read_excel(self.subscale_path, sheet_name=None)
        return {
            "EQ": subscale_raw.get("EQ", pd.DataFrame()),
            "FLA": subscale_raw.get("Anxiety", subscale_raw.get("FLA", pd.DataFrame())),
            "Strategy": subscale_raw.get("Strategy", pd.DataFrame()),
        }

    def load_train_sheets(self) -> Dict[str, pd.DataFrame]:
        train_raw = pd.read_excel(self.train_path, sheet_name=None)
        return {
            "EQ": train_raw.get("EQ", pd.DataFrame()),
            "FLA": train_raw.get("Anxiety", train_raw.get("FLA", pd.DataFrame())),
            "Strategy": train_raw.get("Strategy", pd.DataFrame()),
        }

    def build_item_bank(
        self,
    ) -> Tuple[Dict[str, ItemMeta], Dict[str, List[ItemMeta]], Dict[str, Dict[str, List[int]]]]:
        survey = self.load_survey_sheets()
        subscale = self.load_subscale_sheets()

        reverse_coded = {
            "EQ": self._parse_reverse_rows(subscale["EQ"]),
            "FLA": self._parse_reverse_rows(subscale["FLA"]),
        }

        all_items: Dict[str, ItemMeta] = {}
        grouped: Dict[str, List[ItemMeta]] = {"EQ": [], "FLA": []}
        subscale_map = {"EQ": {}, "FLA": {}, "Strategy": {}}

        for scale in ("EQ", "FLA"):
            mapping_rows = self._extract_subscale_rows(subscale[scale], scale)
            survey_df = survey[scale]
            for sub_name, item_numbers, local_reverse in mapping_rows:
                if "역코딩" in str(sub_name):
                    continue
                subscale_map[scale].setdefault(sub_name, [])
                for item_num in item_numbers:
                    text = self._get_item_text(survey_df, item_num)
                    if not text:
                        continue
                    is_reverse = item_num in reverse_coded[scale] or item_num in local_reverse
                    meta = ItemMeta(
                        scale=scale,
                        item_number=item_num,
                        subscale=sub_name,
                        text=text,
                        reverse_coded=is_reverse,
                    )
                    if meta.question_id not in all_items:
                        all_items[meta.question_id] = meta
                        grouped[scale].append(meta)
                    if item_num not in subscale_map[scale][sub_name]:
                        subscale_map[scale][sub_name].append(item_num)

        strategy_rows = self._extract_subscale_rows(subscale["Strategy"], "Strategy")
        for sub_name, item_numbers, _ in strategy_rows:
            if "역코딩" in str(sub_name):
                continue
            subscale_map["Strategy"][sub_name] = item_numbers

        return all_items, grouped, subscale_map

    def _parse_reverse_rows(self, subscale_df: pd.DataFrame) -> Set[int]:
        reverse_items: Set[int] = set()
        if subscale_df.empty:
            return reverse_items

        for _, row in subscale_df.iterrows():
            row_text = " ".join(str(x) for x in row.values if pd.notna(x))
            if "역코딩" not in row_text:
                continue
            reverse_items.update(num for num, _ in self._parse_item_numbers(str(row.get("해당문항", ""))))

        return reverse_items

    def _extract_subscale_rows(
        self, subscale_df: pd.DataFrame, scale: str
    ) -> List[Tuple[str, List[int], Set[int]]]:
        rows: List[Tuple[str, List[int], Set[int]]] = []
        if subscale_df.empty:
            return rows

        if scale == "EQ":
            sub_col = "하위영역"
        else:
            sub_col = "Anxiety" if "Anxiety" in subscale_df.columns else scale
            if sub_col not in subscale_df.columns:
                sub_col = subscale_df.columns[0]

        for _, row in subscale_df.iterrows():
            sub_name = str(row.get(sub_col, "")).strip()
            if not sub_name:
                continue
            parsed = self._parse_item_numbers(str(row.get("해당문항", "")))
            item_numbers = [num for num, _ in parsed]
            reverse = {num for num, flag in parsed if flag}
            rows.append((sub_name, item_numbers, reverse))
        return rows

    def _get_item_text(self, survey_df: pd.DataFrame, item_number: int) -> str:
        if survey_df.empty:
            return ""
        candidates = survey_df[survey_df["문항"] == item_number]
        if candidates.empty:
            return ""
        return str(candidates.iloc[0]["내용"]).strip()

    def _parse_item_numbers(self, raw: str) -> List[Tuple[int, bool]]:
        results: List[Tuple[int, bool]] = []
        for token in raw.replace("/", ",").split(","):
            t = token.strip()
            if not t:
                continue
            is_reverse = "*" in t
            cleaned = t.replace("*", "").strip()
            if cleaned.isdigit():
                results.append((int(cleaned), is_reverse))
        return results
