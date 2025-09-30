import requests
from backend import config
import asyncio
import logging

def build_mistral_messages(user_text: str):
    messages = []
    if config.MISTRAL_SYSTEM_PROMPT:
        messages.append({"role": "system", "content": config.MISTRAL_SYSTEM_PROMPT})
    messages.append({"role": "user", "content": user_text})
    return messages

class AIService:
    def __init__(self):
        self.logger = logging.getLogger("AIService")

    async def call_mistral(self, prompt: str):
        prompt = (prompt or "").strip()
        if not prompt or not config.MISTRAL_API_KEY:
            return None
        def _request():
            headers = {
                "Authorization": f"Bearer {config.MISTRAL_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": config.MISTRAL_MODEL,
                "messages": build_mistral_messages(prompt),
            }
            try:
                response = requests.post(
                    config.MISTRAL_CHAT_URL,
                    headers=headers,
                    json=payload,
                    timeout=config.MISTRAL_TIMEOUT,
                )
            except requests.RequestException as exc:
                self.logger.warning(f"Mistral request failed: {exc}")
                return None
            if response.status_code >= 400:
                self.logger.warning(f"Mistral returned error {response.status_code}: {response.text[:200]}")
                return None
            try:
                data = response.json()
            except ValueError:
                self.logger.warning(f"Mistral returned non-JSON payload: {response.text[:200]}")
                return None
            choices = data.get("choices") or []
            message = choices[0].get("message") if choices else None
            content = (message or {}).get("content", "").strip()
            return content or None
        try:
            return await asyncio.to_thread(_request)
        except Exception:
            self.logger.exception("Unexpected error while calling Mistral")
            return None
