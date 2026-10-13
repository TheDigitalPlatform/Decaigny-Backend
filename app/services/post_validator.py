import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set

from app.models.dealership_profile import DealershipProfile
from app.services.vehicle_formatter import FormattedVehicle, POST_TYPE_NEW

MAX_HEADLINE = 100
MAX_HASHTAGS = 8
BODY_LIMITS = {"new_vehicle": (200, 1200), "sold_vehicle": (100, 800)}
SOLD_KEYWORDS = {"nl": ("verkocht",), "fr": ("vendu",), "en": ("sold",)}
THANKS_KEYWORDS = {
    "nl": ("bedankt", "dank", "proficiat", "gefeliciteerd", "rijplezier"),
    "fr": ("merci", "félicitations", "bonne route"),
    "en": ("thank", "congratulations", "enjoy"),
}
PLACEHOLDER_RE = re.compile(r"\[[^\]]*\]|\{\{.*?\}\}|\$[a-z_]+|<[^>]+>|\bTBD\b|\bXXX\b|lorem ipsum", re.IGNORECASE)
MARKDOWN_RE = re.compile(r"\*\*|__|`{3}|^\s{0,3}#{1,6}\s", re.MULTILINE)
INLINE_HASHTAG_RE = re.compile(r"(?:^|\s)#[^\s#]+")
HASHTAG_STRIP_RE = re.compile(r"[^\w]", re.UNICODE)
NUMBER_RE = re.compile(r"\d{1,3}(?:[.,\u00a0 ]\d{3})+|\d+")


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    headline: str = ""
    body: str = ""
    call_to_action: str = ""
    hashtags: List[str] = field(default_factory=list)


def _normalize_hashtags(values: Any, defaults: List[str]) -> List[str]:
    raw = list(defaults or []) + (list(values) if isinstance(values, list) else [])
    result, seen = [], set()
    for value in raw:
        tag = HASHTAG_STRIP_RE.sub("", str(value))
        if not tag or tag.lower() in seen:
            continue
        seen.add(tag.lower())
        result.append(f"#{tag}")
    return result[:MAX_HASHTAGS]


def _numbers(text: str) -> Set[str]:
    return {re.sub(r"\D", "", match) for match in NUMBER_RE.findall(text)}


def assemble_content(result: ValidationResult, profile: DealershipProfile) -> str:
    pieces = [result.headline, result.body, result.call_to_action]
    if result.hashtags:
        pieces.append(" ".join(result.hashtags))
    if profile.signature:
        pieces.append(profile.signature)
    return "\n".join(part for part in pieces if part)


def validate_post(
    data: Dict[str, Any],
    *,
    post_type: str,
    formatted: FormattedVehicle,
    language: str,
    profile: DealershipProfile,
) -> ValidationResult:
    headline = str(data.get("headline") or "").strip()
    body = str(data.get("body") or "").strip()
    cta = str(data.get("call_to_action") or "").strip()
    hashtags = _normalize_hashtags(data.get("hashtags"), profile.hashtags or [])
    full_text = "\n".join((headline, body, cta))
    low = full_text.lower()
    errors: List[str] = []

    if not headline:
        errors.append("headline is empty")
    elif len(headline) > MAX_HEADLINE:
        errors.append(f"headline must be at most {MAX_HEADLINE} characters (got {len(headline)})")

    min_len, max_len = BODY_LIMITS[post_type]
    if not min_len <= len(body) <= max_len:
        errors.append(f"body must be {min_len}-{max_len} characters (got {len(body)})")
    if PLACEHOLDER_RE.search(full_text):
        errors.append("post contains placeholders or unreadable tokens")
    if MARKDOWN_RE.search(body):
        errors.append("body contains markdown or headings")
    if not cta:
        errors.append("call_to_action is empty")
    if len(hashtags) < 3:
        errors.append("at least 3 hashtags are required")
    if len(hashtags) > MAX_HASHTAGS:
        errors.append(f"hashtags must be at most {MAX_HASHTAGS} (got {len(hashtags)})")
    if not INLINE_HASHTAG_RE.search(full_text) and not hashtags:
        errors.append("hashtags are missing")

    if post_type == POST_TYPE_NEW:
        if formatted.make and formatted.model and formatted.make.lower() not in low and formatted.model.lower() not in low:
            errors.append("headline or body must mention the make/model")
        expected_numbers = {str(int(value)) for value in [formatted.vehicle_id] if value}
        if formatted.price and formatted.price not in body and formatted.price not in full_text:
            errors.append("new vehicle posts should mention the price when provided")
        if formatted.mileage and formatted.mileage not in body and formatted.mileage not in full_text:
            errors.append("new vehicle posts should mention the mileage when provided")
    else:
        sold_words = SOLD_KEYWORDS.get(language, SOLD_KEYWORDS["en"])
        if not any(word in low for word in sold_words):
            errors.append("sold vehicle posts must include the sold wording")
        if any(keyword in low for keyword in THANKS_KEYWORDS.get(language, THANKS_KEYWORDS["en"])) is False:
            errors.append("sold vehicle posts must thank the customer or acknowledge their trust")
        if formatted.price and formatted.price in full_text:
            errors.append("sold posts must never mention a price")
        if formatted.mileage and formatted.mileage in full_text:
            errors.append("sold posts must never mention mileage")
    if not set(_numbers(body)).issubset(set(_numbers(full_text))):
        pass

    return ValidationResult(
        is_valid=not errors,
        errors=errors,
        headline=headline,
        body=body,
        call_to_action=cta,
        hashtags=hashtags,
    )
