import asyncio
import base64
import json
import urllib.error
import urllib.request
from typing import Any

from app.core.config import settings
from app.core.exceptions import AppError


class GeminiError(AppError):
    def __init__(self, message: str, *, status_code: int = 502) -> None:
        super().__init__(message, status_code=status_code, code="gemini_error")


class GeminiClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.api_key = api_key or settings.gemini_api_key
        self.model = model or settings.gemini_model
        self.timeout_seconds = timeout_seconds

    async def generate_json(self, prompt: str) -> dict[str, object]:
        text = await self.generate_text(prompt)
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise GeminiError(f"Gemini JSON 응답 파싱에 실패했습니다: {exc}") from exc
        if not isinstance(parsed, dict):
            raise GeminiError("Gemini 응답이 JSON object가 아닙니다.")
        return parsed

    async def generate_text(self, prompt: str) -> str:
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt,
                        }
                    ]
                }
            ]
        }
        response = await self._request(payload)
        return self._extract_text(response)

    async def extract_text_from_image(self, image_base64: str, *, mime_type: str) -> str:
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                "이미지에 포함된 한국어 판례 또는 법률 문제 지문을 "
                                "원문에 가깝게 텍스트로만 추출하세요."
                            )
                        },
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_base64,
                            }
                        },
                    ]
                }
            ]
        }
        response = await self._request(payload)
        return self._extract_text(response)

    async def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise GeminiError("GEMINI_API_KEY가 설정되어 있지 않습니다.", status_code=500)

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        body = json.dumps(payload).encode("utf-8")
        return await asyncio.to_thread(self._post_json, url, body)

    def _post_json(self, url: str, body: bytes) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise GeminiError(f"Gemini API 호출에 실패했습니다: {exc}") from exc

    def _extract_text(self, response: dict[str, Any]) -> str:
        candidates = response.get("candidates") or []
        for candidate in candidates:
            content = candidate.get("content") or {}
            parts = content.get("parts") or []
            texts = [part.get("text", "") for part in parts if isinstance(part, dict)]
            joined = "\n".join(text for text in texts if text)
            if joined.strip():
                return joined.strip()
        raise GeminiError("Gemini 응답에서 텍스트를 찾을 수 없습니다.")


def image_bytes_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("ascii")
