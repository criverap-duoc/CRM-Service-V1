## crm_service\apps\integrations\clients.py
import logging
import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

META_GRAPH_URL = "https://graph.facebook.com/v20.0"
OPENAI_URL = "https://api.openai.com/v1"


class MetaClient:
    def __init__(self, access_token=None):
        self.access_token = access_token or settings.META_ACCESS_TOKEN

    def get_leads(self, form_id, limit=25):
        url = f"{META_GRAPH_URL}/{form_id}/leads"
        params = {"limit": limit, "access_token": self.access_token}
        try:
            response = httpx.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error("Meta API error [%s]: %s", exc.response.status_code, exc.response.text)
            raise
        except httpx.RequestError as exc:
            logger.error("Meta API connection error: %s", exc)
            raise


class OpenAIClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or settings.OPENAI_API_KEY

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat(self, messages, model="gpt-4o-mini", max_tokens=512):
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        try:
            response = httpx.post(
                f"{OPENAI_URL}/chat/completions",
                headers=self._headers(),
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as exc:
            logger.error("OpenAI API error [%s]: %s", exc.response.status_code, exc.response.text)
            raise
        except httpx.RequestError as exc:
            logger.error("OpenAI connection error: %s", exc)
            raise

    def summarize_interaction(self, body):
        return self.chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a CRM assistant. Summarize the following customer interaction "
                        "in 2-3 sentences, highlighting key intent and any action items."
                    ),
                },
                {"role": "user", "content": body},
            ]
        )
