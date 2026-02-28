from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "Data"
CACHE_DIR = PROJECT_ROOT / "backend" / ".cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

SURVEY_FILE = DATA_DIR / "Survey.xlsx"
SUBSCALE_FILE_CANDIDATES = [
    DATA_DIR / "Subscal.xlsx",
    DATA_DIR / "Subscale.xlsx",
]
TRAIN_FILE = DATA_DIR / "Train_test_balanced.xlsx"

TARGET_SHORT_ITEMS = {"EQ": 45, "FLA": 12}
SIMILARITY_THRESHOLD = 0.80
MIN_CRONBACH_ALPHA = 0.70
LIKERT_MIN = 1
LIKERT_MAX = 5
TIE_GAP_THRESHOLD = 0.10
MAX_REQUESTION_ROUNDS = 3
