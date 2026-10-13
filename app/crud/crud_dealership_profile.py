from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.dealership_profile import DealershipProfile


def get_active(db: Session) -> Optional[DealershipProfile]:
    return (
        db.query(DealershipProfile)
        .filter(DealershipProfile.is_active.is_(True))
        .order_by(DealershipProfile.id)
        .first()
    )


def update_profile(db: Session, profile: DealershipProfile, values: Dict[str, Any]) -> DealershipProfile:
    for field, value in values.items():
        setattr(profile, field, value)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
