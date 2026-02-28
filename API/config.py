# API/config.py
from pathlib import Path
from dotenv import load_dotenv
import os

def load_openai_key() -> str:
    here = Path(__file__).parent
    # 우선순위: 환경변수 > API/api.env > 프로젝트 루트 .env
    candidates = [here / "api.env", here.parent / ".env"]
    for p in candidates:
        if p.exists():
            load_dotenv(p)

    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY가 설정되지 않았습니다. "
            "환경변수로 넣거나 API/api.env(.env)에 추가하세요."
        )
    return key

def load_openai_model(default: str = "gpt-4o") -> str:
    # 필요시 환경변수로 모델 바꿀 수 있게
    return os.getenv("OPENAI_MODEL", default)