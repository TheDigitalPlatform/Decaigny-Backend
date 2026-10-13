from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

from app.models.vehicle import Vehicle

POST_TYPE_NEW = "new_vehicle"
POST_TYPE_SOLD = "sold_vehicle"
MAX_KEY_FEATURES = 6

FUEL_LABELS = {
    "nl": {"petrol": "Benzine", "diesel": "Diesel", "electric": "Elektrisch", "hybrid": "Hybride", "lpg": "LPG", "cng": "CNG"},
    "fr": {"petrol": "Essence", "diesel": "Diesel", "electric": "Électrique", "hybrid": "Hybride", "lpg": "LPG", "cng": "CNG"},
    "en": {"petrol": "Petrol", "diesel": "Diesel", "electric": "Electric", "hybrid": "Hybrid", "lpg": "LPG", "cng": "CNG"},
}
TRANSMISSION_LABELS = {
    "nl": {"automatic": "Automaat", "manual": "Manueel"},
    "fr": {"automatic": "Automatique", "manual": "Manuelle"},
    "en": {"automatic": "Automatic", "manual": "Manual"},
}
FEATURE_PRIORITY_KEYWORDS = (
    "navigat", "gps", "camera", "360", "leder", "leather", "cuir", "panora", "adaptie", "adaptive",
    "cruise", "carplay", "android auto", "led", "matrix", "xenon", "verwarm", "heated", "chauffant",
    "head-up", "trekhaak", "towbar", "attelage", "keyless", "parkeer", "parking", "sport", "velgen",
    "jantes", "alloy", "elektrische koffer", "hayon",
)


def _group_thousands(amount: int, language: str) -> str:
    return f"{amount:,}".replace(",", "," if language == "en" else ".")


def format_price(value: Any, language: str) -> Optional[str]:
    if value is None:
        return None
    try:
        amount = int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError):
        return None
    if amount <= 0:
        return None
    grouped = _group_thousands(amount, language)
    return f"€{grouped}" if language == "en" else f"€ {grouped}"


def format_mileage(value: Optional[int], language: str) -> Optional[str]:
    if value is None or value < 0:
        return None
    return f"{_group_thousands(int(value), language)} km"


def _label(mapping: Dict[str, Dict[str, str]], language: str, value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return mapping.get(language, mapping["en"]).get(value.lower(), value.capitalize())


def select_key_features(features: Any, limit: int = MAX_KEY_FEATURES) -> List[str]:
    if not isinstance(features, list):
        return []
    seen, cleaned = set(), []
    for item in features:
        text = str(item).strip()
        if not text or len(text) > 60 or text.lower() in seen:
            continue
        seen.add(text.lower())
        cleaned.append(text)

    def score(text: str) -> int:
        low = text.lower()
        return sum(1 for keyword in FEATURE_PRIORITY_KEYWORDS if keyword in low)

    ranked = sorted(enumerate(cleaned), key=lambda pair: (-score(pair[1]), pair[0]))
    return [text for _, text in ranked[:limit]]


@dataclass
class FormattedVehicle:
    vehicle_id: int
    post_type: str
    language: str
    make: Optional[str]
    model: Optional[str]
    title: str
    facts: Dict[str, str] = field(default_factory=dict)
    key_features: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)

    @property
    def has_identity(self) -> bool:
        return bool(self.make and self.model)

    @property
    def price(self) -> Optional[str]:
        return self.facts.get("Price")

    @property
    def mileage(self) -> Optional[str]:
        return self.facts.get("Mileage")

    def to_prompt_block(self) -> str:
        lines = [f"Vehicle: {self.title}"]
        lines += [f"{label}: {value}" for label, value in self.facts.items()]
        if self.key_features:
            lines.append("Key features:")
            lines += [f"- {feature}" for feature in self.key_features]
        if self.missing_fields:
            lines.append(f"Not provided (do NOT mention): {', '.join(self.missing_fields)}")
        return "\n".join(lines)


def format_vehicle(vehicle: Vehicle, language: str, post_type: str) -> FormattedVehicle:
    title = " ".join(str(part) for part in (vehicle.make, vehicle.model, vehicle.trim) if part)
    facts: Dict[str, Optional[str]] = {}
    if post_type == POST_TYPE_NEW:
        facts["Price"] = format_price(vehicle.price, language)
        facts["Mileage"] = format_mileage(vehicle.mileage, language)
    facts.update(
        {
            "Year": str(vehicle.year) if vehicle.year else None,
            "Fuel type": _label(FUEL_LABELS, language, vehicle.fuel_type),
            "Transmission": _label(TRANSMISSION_LABELS, language, vehicle.transmission),
            "Body type": vehicle.body_type,
            "Color": vehicle.color,
        }
    )

    return FormattedVehicle(
        vehicle_id=vehicle.id,
        post_type=post_type,
        language=language,
        make=vehicle.make,
        model=vehicle.model,
        title=title,
        facts={label: value for label, value in facts.items() if value},
        key_features=select_key_features(vehicle.features) if post_type == POST_TYPE_NEW else [],
        missing_fields=[label for label, value in facts.items() if not value],
    )
