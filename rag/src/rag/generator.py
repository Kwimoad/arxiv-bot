import os

import requests

from ...config import OPENROUTER_API_KEY


class Generator:
    def __init__(self, api_key: str | None = None, model: str = "openai/gpt-4o-mini"):

        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or OPENROUTER_API_KEY
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY est absente. Définissez-la dans .env ou dans l'environnement."
            )
        self.model = model
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    def generate(self, prompt: str) -> str:

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }

        response = requests.post(self.url, headers=headers, json=payload, timeout=120)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            if response.status_code in (401, 403):
                raise RuntimeError(
                    "La clé OPENROUTER_API_KEY est invalide ou expirée. "
                    "Remplacez-la dans api_keys.env puis redémarrez le serveur."
                ) from error
            raise

        data = response.json()

        return data["choices"][0]["message"]["content"]
