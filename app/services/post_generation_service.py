import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.crud import crud_dealership_profile, crud_generated_post, crud_prompt, crud_settings
from app.crud.crud_ai_generation_log import create_log
from app.models.generated_post import GeneratedPost
from app.models.vehicle import Vehicle
from app.services.claude_client import ClaudeClient, ClaudeClientError, claude_client
from app.services.post_validator import ValidationResult, assemble_content, validate_post
from app.services.prompt_builder import build_prompt, resolve_tone
from app.services.vehicle_formatter import POST_TYPE_NEW, POST_TYPE_SOLD, format_vehicle

logger = logging.getLogger(__name__)


class PostGenerationService:
    def __init__(self, claude_client_instance: Optional[ClaudeClient] = None):
        self.claude_client = claude_client_instance or claude_client

    def _resolve_post_type(self, vehicle: Vehicle, requested: Optional[str]) -> str:
        if requested in {POST_TYPE_NEW, POST_TYPE_SOLD}:
            return requested
        if vehicle.status == "sold" or vehicle.issold:
            return POST_TYPE_SOLD
        return POST_TYPE_NEW

    def _resolve_language(self, db: Session, vehicle: Vehicle, requested: Optional[str]) -> str:
        if requested:
            return requested.strip().lower()
        profile = crud_dealership_profile.get_active(db)
        if profile and profile.default_language:
            return profile.default_language.strip().lower()
        return "nl"

    def _resolve_profile(self, db: Session):
        profile = crud_dealership_profile.get_active(db)
        if not profile:
            from app.models.dealership_profile import DealershipProfile

            profile = DealershipProfile(
                name="Decaigny",
                default_language="nl",
                call_to_action="Plan vandaag nog je proefrit of kom langs in onze showroom.",
                hashtags=["#Decaigny", "#Tweedehandswagen"],
                banned_phrases=["goedkoopste van België", "laagste prijs gegarandeerd", "gratis"],
                use_emojis=True,
                is_active=True,
            )
            db.add(profile)
            db.flush()
        return profile

    def generate_post_for_vehicle(
        self,
        db: Session,
        vehicle: Vehicle,
        *,
        post_type: Optional[str] = None,
        tone: Optional[str] = None,
        tone_id: Optional[int] = None,
        language: Optional[str] = None,
        source: str = "manual",
        validation_feedback: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        resolved_post_type = self._resolve_post_type(vehicle, post_type)
        resolved_language = self._resolve_language(db, vehicle, language)
        profile = self._resolve_profile(db)
        chosen_tone = resolve_tone(db, resolved_post_type, tone=tone, tone_id=tone_id)
        formatted = format_vehicle(vehicle, resolved_language, resolved_post_type)
        prompt = build_prompt(
            db,
            formatted=formatted,
            post_type=resolved_post_type,
            tone=chosen_tone,
            profile=profile,
            language=resolved_language,
            validation_feedback=validation_feedback,
        )

        validation_errors: Optional[List[str]] = None
        previous_data: Optional[Dict[str, Any]] = None
        for attempt in range(1, settings_max_retries() + 2):
            try:
                result = self.claude_client.generate_post(prompt.system_prompt, prompt.user_prompt)
                data = result.data
                validation = validate_post(
                    data,
                    post_type=resolved_post_type,
                    formatted=formatted,
                    language=resolved_language,
                    profile=profile,
                )
                if validation.is_valid:
                    previous_data = data
                    validation_errors = None
                    break
                validation_errors = validation.errors
                prompt = build_prompt(
                    db,
                    formatted=formatted,
                    post_type=resolved_post_type,
                    tone=chosen_tone,
                    profile=profile,
                    language=resolved_language,
                    validation_feedback=validation.errors,
                )
                if attempt >= settings_max_retries() + 1:
                    break
            except ClaudeClientError as exc:
                raise exc

        if validation_errors is not None and previous_data is None:
            raise ClaudeClientError(
                "Claude output failed validation after retry",
                "AI_VALIDATION_FAILED",
                502,
                False,
            )

        if previous_data is None:
            previous_data = {"headline": "", "body": "", "call_to_action": "", "hashtags": []}

        final_payload = previous_data
        validation = validate_post(
            final_payload,
            post_type=resolved_post_type,
            formatted=formatted,
            language=resolved_language,
            profile=profile,
        )
        if not validation.is_valid:
            create_log(
                db,
                vehicle_id=vehicle.id,
                post_type=resolved_post_type,
                tone_name=chosen_tone.name,
                language=resolved_language,
                source=source,
                status="validation_failed",
                attempt=max(1, len(validation.errors) or 1),
                ai_model=getattr(self.claude_client, "model", None),
                system_prompt=prompt.system_prompt,
                user_prompt=prompt.user_prompt,
                raw_response=str(final_payload),
                validation_errors=validation.errors,
                error_code="AI_VALIDATION_FAILED",
                error_message="Claude output failed validation",
            )
            raise ClaudeClientError("Claude output failed validation", "AI_VALIDATION_FAILED", 502, False)

        post = crud_generated_post.create_post_version(
            db,
            vehicle_id=vehicle.id,
            post_type=resolved_post_type,
            values={
                "tone_prompt_id": chosen_tone.id,
                "tone_name": chosen_tone.name,
                "language": resolved_language,
                "headline": validation.headline,
                "body": validation.body,
                "call_to_action": validation.call_to_action,
                "hashtags": validation.hashtags,
                "content": assemble_content(validation, profile),
                "status": "draft",
                "ai_model": getattr(self.claude_client, "model", None),
            },
        )
        db.commit()
        create_log(
            db,
            vehicle_id=vehicle.id,
            generated_post_id=post.id,
            post_type=resolved_post_type,
            tone_name=chosen_tone.name,
            language=resolved_language,
            source=source,
            status="success",
            attempt=1,
            ai_model=getattr(self.claude_client, "model", None),
            system_prompt=prompt.system_prompt,
            user_prompt=prompt.user_prompt,
            raw_response=str(final_payload),
            validation_errors=None,
            error_code=None,
            error_message=None,
        )
        return {
            "id": post.id,
            "vehicle_id": vehicle.id,
            "post_type": resolved_post_type,
            "tone_name": chosen_tone.name,
            "language": resolved_language,
            "headline": validation.headline,
            "body": validation.body,
            "call_to_action": validation.call_to_action,
            "hashtags": validation.hashtags,
            "content": post.content,
            "status": post.status,
            "version": post.version,
            "is_current": post.is_current,
        }


service = PostGenerationService()


def settings_max_retries() -> int:
    from app.core.config import settings

    return int(getattr(settings, "AI_MAX_VALIDATION_RETRIES", 1) or 1)
