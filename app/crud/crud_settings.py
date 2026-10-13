from typing import Optional
from sqlalchemy.orm import Session
from app.models.app_setting import AppSetting

DEFAULT_COMMUNICATION_STYLE_KEY = "default_communication_style"
AI_TONE_KEYS = {
    "new_vehicle": "ai_new_vehicle_tone",
    "sold_vehicle": "ai_sold_vehicle_tone",
}


def get_setting(db: Session, key: str) -> Optional[AppSetting]:
    return db.query(AppSetting).filter(AppSetting.key == key).first()


def set_setting(db: Session, key: str, value: Optional[str]) -> AppSetting:
    setting = get_setting(db, key)
    if setting:
        setting.value = value
    else:
        setting = AppSetting(key=key, value=value)
        db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


def get_default_communication_style(db: Session) -> Optional[str]:
    setting = get_setting(db, DEFAULT_COMMUNICATION_STYLE_KEY)
    return setting.value if setting else None


def set_default_communication_style(db: Session, value: str) -> AppSetting:
    return set_setting(db, DEFAULT_COMMUNICATION_STYLE_KEY, value)


def get_ai_tone_for_post_type(db: Session, post_type: str) -> Optional[str]:
    key = AI_TONE_KEYS.get(post_type)
    if not key:
        return None
    setting = get_setting(db, key)
    return setting.value if setting else None


def set_ai_tone_for_post_type(db: Session, post_type: str, value: str) -> AppSetting:
    key = AI_TONE_KEYS.get(post_type)
    if not key:
        raise KeyError(f"Unsupported post type: {post_type}")
    return set_setting(db, key, value)
