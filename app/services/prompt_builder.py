from dataclasses import dataclass
from string import Template
from typing import List, Optional

from sqlalchemy.orm import Session

from app.crud import crud_prompt, crud_settings
from app.models.dealership_profile import DealershipProfile
from app.models.prompt import Prompt
from app.services.vehicle_formatter import FormattedVehicle, POST_TYPE_NEW, POST_TYPE_SOLD

PROMPT_TYPE_TONE = "tone"
PROMPT_TYPE_SYSTEM = "system"
PROMPT_TYPE_NEW_TEMPLATE = "new_vehicle_template"
PROMPT_TYPE_SOLD_TEMPLATE = "sold_vehicle_template"

TEMPLATE_TYPE_BY_POST = {
    POST_TYPE_NEW: PROMPT_TYPE_NEW_TEMPLATE,
    POST_TYPE_SOLD: PROMPT_TYPE_SOLD_TEMPLATE,
}
FALLBACK_TONE_BY_POST = {POST_TYPE_NEW: "Professional", POST_TYPE_SOLD: "Friendly"}
LANGUAGE_NAMES = {"nl": "Dutch (Belgian Flemish)", "fr": "French (Belgian)", "en": "English"}


class PromptConfigError(Exception):
    def __init__(self, message: str, error_code: str):
        super().__init__(message)
        self.error_code = error_code


@dataclass
class BuiltPrompt:
    system_prompt: str
    user_prompt: str


def _as_active_tone(prompt: Optional[Prompt]) -> Optional[Prompt]:
    if prompt and prompt.is_active and prompt.prompt_type == PROMPT_TYPE_TONE:
        return prompt
    return None


def resolve_tone(db: Session, post_type: str, tone: Optional[str] = None, tone_id: Optional[int] = None) -> Prompt:
    if tone_id is not None or tone:
        found = _as_active_tone(
            crud_prompt.get_prompt(db, tone_id) if tone_id is not None else crud_prompt.get_prompt_by_name_ci(db, tone)
        )
        if not found:
            raise PromptConfigError(f"Tone '{tone_id or tone}' does not exist or is inactive", "TONE_NOT_FOUND")
        return found

    for value in (
        crud_settings.get_ai_tone_for_post_type(db, post_type),
        crud_settings.get_default_communication_style(db),
        FALLBACK_TONE_BY_POST[post_type],
    ):
        found = _as_active_tone(crud_prompt.get_prompt_by_id_or_name(db, value))
        if found:
            return found
    raise PromptConfigError("No active tone is configured", "TONE_NOT_FOUND")


def get_active_template(db: Session, prompt_type: str) -> Prompt:
    prompt = crud_prompt.get_active_by_type(db, prompt_type)
    if not prompt:
        raise PromptConfigError(f"No active prompt of type '{prompt_type}'", "TEMPLATE_NOT_FOUND")
    return prompt


def _dealership_block(profile: DealershipProfile) -> str:
    lines = [f"Dealership name: {profile.name}"]
    for label, value in (
        ("Location", profile.location),
        ("Website", profile.website),
        ("Phone", profile.phone),
        ("Tagline", profile.tagline),
    ):
        if value:
            lines.append(f"{label}: {value}")
    if profile.preferred_phrases:
        lines.append(
            "Dealership phrases (weave in at most one, only where natural): "
            + " | ".join(profile.preferred_phrases)
        )
    lines.append("Emojis: allowed, follow the tone guidance" if profile.use_emojis else "Emojis: do NOT use any emojis")
    return "\n".join(lines)


def build_prompt(
    db: Session,
    *,
    formatted: FormattedVehicle,
    post_type: str,
    tone: Prompt,
    profile: DealershipProfile,
    language: str,
    validation_feedback: Optional[List[str]] = None,
) -> BuiltPrompt:
    system_template = get_active_template(db, PROMPT_TYPE_SYSTEM)
    post_template = get_active_template(db, TEMPLATE_TYPE_BY_POST[post_type])

    base_vars = {
        "dealership_name": profile.name,
        "dealership_location": profile.location or "our region",
        "language_name": LANGUAGE_NAMES.get(language, LANGUAGE_NAMES["nl"]),
        "banned_phrases": ", ".join(f'"{p}"' for p in (profile.banned_phrases or [])) or "(none)",
        "call_to_action": profile.call_to_action or "Contact us or visit our showroom.",
        "default_hashtags": " ".join(profile.hashtags or []) or "(none)",
    }
    variables = {
        **base_vars,
        "tone_name": tone.name,
        "tone_instructions": Template(tone.content).safe_substitute(base_vars),
        "dealership_block": _dealership_block(profile),
        "vehicle_block": formatted.to_prompt_block(),
    }

    system_prompt = Template(system_template.content).safe_substitute(variables)
    user_prompt = Template(post_template.content).safe_substitute(variables)
    if validation_feedback:
        user_prompt += (
            "\n\nYOUR PREVIOUS DRAFT WAS REJECTED FOR THESE REASONS:\n"
            + "\n".join(f"- {error}" for error in validation_feedback)
            + "\nWrite a new draft that fixes every point."
        )
    return BuiltPrompt(system_prompt=system_prompt, user_prompt=user_prompt)
