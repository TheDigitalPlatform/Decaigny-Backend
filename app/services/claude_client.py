import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import anthropic

from app.core.config import settings

logger = logging.getLogger(__name__)

POST_TOOL: Dict[str, Any] = {
    "name": "submit_facebook_post",
    "description": "Submit the finished Facebook post draft.",
    "input_schema": {
        "type": "object",
        "properties": {
            "headline": {"type": "string", "description": "Short hook line, max 80 characters, no hashtags."},
            "body": {"type": "string", "description": "Main post text. Plain text, no markdown, no hashtags."},
            "call_to_action": {"type": "string", "description": "One closing call-to-action sentence."},
            "hashtags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "3-6 hashtags, each starting with #.",
            },
        },
        "required": ["headline", "body", "call_to_action", "hashtags"],
    },
}


class ClaudeClientError(Exception):
    def __init__(
        self,
        message: str,
        error_code: str = "AI_API_ERROR",
        http_status: int = 502,
        retryable: bool = False,
        retry_after: Optional[int] = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.http_status = http_status
        self.retryable = retryable
        self.retry_after = retry_after


@dataclass
class ClaudeResult:
    data: Dict[str, Any]
    raw_text: str
    model: str
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    latency_ms: int
    request_id: Optional[str]


def _retry_after(exc: anthropic.APIStatusError) -> Optional[int]:
    value = exc.response.headers.get("retry-after") if exc.response is not None else None
    try:
        return int(float(value)) if value else None
    except ValueError:
        return None


class ClaudeClient:
    """Anthropic Messages API client. Reads configuration exclusively from settings / .env."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        self.api_key = (api_key or settings.ANTHROPIC_API_KEY).strip()
        self.model = model or settings.ANTHROPIC_MODEL
        self.max_tokens = max_tokens or settings.ANTHROPIC_MAX_TOKENS
        self.temperature = settings.ANTHROPIC_TEMPERATURE if temperature is None else temperature
        self.timeout = timeout or settings.ANTHROPIC_TIMEOUT_SECONDS
        self.max_retries = settings.ANTHROPIC_MAX_RETRIES if max_retries is None else max_retries
        self._client: Optional[anthropic.Anthropic] = None

    def _get_client(self) -> anthropic.Anthropic:
        if not self.api_key:
            raise ClaudeClientError(
                "ANTHROPIC_API_KEY is not configured. Set it in .env and restart the server.",
                error_code="AI_NOT_CONFIGURED",
                http_status=503,
            )
        if self._client is None:
            self._client = anthropic.Anthropic(
                api_key=self.api_key,
                timeout=self.timeout,
                max_retries=self.max_retries,
            )
        return self._client

    def generate_post(self, system_prompt: str, user_prompt: str) -> ClaudeResult:
        client = self._get_client()
        started = time.monotonic()
        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                tools=[POST_TOOL],
                tool_choice={"type": "tool", "name": POST_TOOL["name"]},
                messages=[{"role": "user", "content": user_prompt}],
            )
        except anthropic.RateLimitError as exc:
            raise ClaudeClientError("Claude rate limit reached", "AI_RATE_LIMITED", 429, True, _retry_after(exc)) from exc
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as exc:
            raise ClaudeClientError("Claude rejected the API key", "AI_AUTH_ERROR", 503) from exc
        except anthropic.BadRequestError as exc:
            raise ClaudeClientError(f"Claude rejected the request: {exc}", "AI_BAD_REQUEST", 502) from exc
        except anthropic.APIStatusError as exc:
            retryable = exc.status_code >= 500
            code = "AI_OVERLOADED" if exc.status_code == 529 else "AI_API_ERROR"
            raise ClaudeClientError(
                f"Claude API error {exc.status_code}", code, 503 if retryable else 502, retryable, _retry_after(exc)
            ) from exc
        except anthropic.APITimeoutError as exc:
            raise ClaudeClientError("Claude request timed out", "AI_TIMEOUT", 504, True) from exc
        except anthropic.APIConnectionError as exc:
            raise ClaudeClientError(f"Claude connection error: {exc}", "AI_CONNECTION_ERROR", 503, True) from exc

        latency_ms = int((time.monotonic() - started) * 1000)
        tool_block = next((block for block in response.content if getattr(block, "type", None) == "tool_use"), None)
        if tool_block is None or response.stop_reason == "max_tokens":
            raise ClaudeClientError(
                f"Claude returned no complete post (stop_reason={response.stop_reason})",
                "AI_INVALID_RESPONSE",
                502,
                True,
            )

        data = dict(tool_block.input)
        logger.info(
            "Claude post generated | model=%s, in=%s, out=%s, latency_ms=%s",
            response.model,
            getattr(response.usage, "input_tokens", None),
            getattr(response.usage, "output_tokens", None),
            latency_ms,
        )
        return ClaudeResult(
            data=data,
            raw_text=json.dumps(data, ensure_ascii=False),
            model=response.model,
            input_tokens=getattr(response.usage, "input_tokens", None),
            output_tokens=getattr(response.usage, "output_tokens", None),
            latency_ms=latency_ms,
            request_id=getattr(response, "_request_id", None),
        )


claude_client = ClaudeClient()
