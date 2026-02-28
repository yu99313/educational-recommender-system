# API/GptAPI.py
from openai import OpenAI
from .config import load_openai_key, load_openai_model

class GptAPI:
    def __init__(self, model: str | None = None, temperature: float = 0.0, max_tokens: int = 2000):
        key = load_openai_key()
        self.client = OpenAI(api_key=key)
        self.model = model or load_openai_model()
        self.temperature = temperature
        self.max_tokens = max_tokens

    def chat(self, system: str, user: str) -> str | None:
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"[GptAPI] chat failed: {e}")
            return None

    # 기존 에이전트 호환용
    def generate_response(self, prompt: str) -> str | None:
        return self.chat(
            "You are a helpful assistant that groups semantically similar Korean questionnaire items.",
            prompt,
        )

    def call_gpt(self, prompt: str) -> str | None:
        return self.generate_response(prompt)