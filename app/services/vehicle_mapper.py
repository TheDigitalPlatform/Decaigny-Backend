import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def _extract_name_or_value(val: Any) -> Optional[str]:
    """Helper to extract string name/value from either a dict or primitive."""
    if val is None:
        return None
    if isinstance(val, dict):
        res = val.get("name") or val.get("value")
        return str(res).strip() if res is not None else None
    return str(val).strip()


def _normalize_transmission(raw_val: Optional[str]) -> Optional[str]:
    if not raw_val:
        return None
    low = raw_val.lower().strip()
    if any(k in low for k in ["auto", "automaat", "automatique", "dsg", "tiptronic", "steptronic"]):
        return "automatic"
    if any(k in low for k in ["man", "handgeschakeld", "manueel", "manuel"]):
        return "manual"
    return low


def _normalize_fuel_type(raw_val: Optional[str]) -> Optional[str]:
    if not raw_val:
        return None
    low = raw_val.lower().strip()
    if any(k in low for k in ["benzine", "petrol", "essence", "gasoline"]):
        return "petrol"
    if "diesel" in low:
        return "diesel"
    if any(k in low for k in ["elektrisch", "electric", "electrique", "ev", "bev"]):
        return "electric"
    if any(k in low for k in ["hybride", "hybrid", "phev", "mhev"]):
        return "hybrid"
    if "lpg" in low:
        return "lpg"
    if "cng" in low:
        return "cng"
    return low


def _parse_decimal(val: Any) -> Optional[Decimal]:
    if val is None or val == "":
        return None
    try:
        # Handle string floats or European comma notation
        if isinstance(val, str):
            clean = val.replace(",", ".").replace("€", "").replace(" ", "").strip()
            return Decimal(clean)
        return Decimal(str(val))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _parse_int(val: Any) -> Optional[int]:
    if val is None or val == "":
        return None
    try:
        if isinstance(val, (int, float)):
            return int(val)
        clean = str(val).replace(".", "").replace(",", "").replace("km", "").replace(" ", "").strip()
        return int(clean)
    except (ValueError, TypeError):
        return None


def _extract_features(options_val: Any) -> List[str]:
    """Extract list of feature/option names."""
    features: List[str] = []
    if isinstance(options_val, list):
        for item in options_val:
            if isinstance(item, dict):
                name = item.get("name") or item.get("value") or item.get("description")
                if name:
                    features.append(str(name).strip())
            elif isinstance(item, str) and item.strip():
                features.append(item.strip())
    elif isinstance(options_val, dict):
        for k, v in options_val.items():
            if isinstance(v, str):
                features.append(v.strip())
            elif isinstance(v, dict):
                n = v.get("name") or v.get("value")
                if n:
                    features.append(str(n).strip())
    return features


def _extract_image_urls(images_val: Any) -> List[str]:
    """Extract list of image URLs from raw YDD images attribute."""
    urls: List[str] = []
    if isinstance(images_val, list):
        for img in images_val:
            if isinstance(img, dict):
                url = img.get("url") or img.get("path") or img.get("link")
                if url and isinstance(url, str) and url.strip():
                    urls.append(url.strip())
            elif isinstance(img, str) and img.strip():
                urls.append(img.strip())
    return urls


def map_ydd_vehicle(raw: Dict[str, Any]) -> Optional[Tuple[Dict[str, Any], List[str]]]:
    """
    Map raw YDD car dictionary to Decaigny vehicle dict + image URLs.
    Returns (vehicle_dict, image_urls) or None if record is invalid (e.g. missing id).
    """
    raw_id = raw.get("id")
    if raw_id is None or str(raw_id).strip() == "":
        logger.warning("Skipping YDD car record without id: %s", raw)
        return None

    erp_id = str(raw_id).strip()
    raw_vin = raw.get("vin")
    vin = str(raw_vin).strip().upper() if raw_vin else None
    stock_number = str(raw.get("reference") or raw.get("stock_number") or "").strip() or None

    make = _extract_name_or_value(raw.get("make"))
    model = _extract_name_or_value(raw.get("model"))
    year = _parse_int(raw.get("modelyear") or raw.get("year"))
    trim = _extract_name_or_value(raw.get("trim") or raw.get("version"))

    # Price preference: commercialprice -> dealerprice -> price
    price = (
        _parse_decimal(raw.get("commercialprice"))
        or _parse_decimal(raw.get("dealerprice"))
        or _parse_decimal(raw.get("price"))
    )
    mileage = _parse_int(raw.get("mileage"))

    fuel_raw = _extract_name_or_value(raw.get("fuel"))
    fuel_type = _normalize_fuel_type(fuel_raw)

    trans_raw = _extract_name_or_value(raw.get("transmission"))
    transmission = _normalize_transmission(trans_raw)

    color = _extract_name_or_value(raw.get("color"))
    body_type = _extract_name_or_value(raw.get("bodytype") or raw.get("body_type"))

    features = _extract_features(raw.get("options") or raw.get("features"))

    issold = bool(raw.get("issold"))
    isonline = bool(raw.get("isonline"))
    isnewinstock = bool(raw.get("isnewinstock"))

    status = "sold" if issold else ("available" if isonline else "available")
    erp_status_raw = f"online={isonline},sold={issold},newinstock={isnewinstock}"

    image_urls = _extract_image_urls(raw.get("images"))

    vehicle_data = {
        "erp_id": erp_id,
        "vin": vin,
        "stock_number": stock_number,
        "make": make,
        "model": model,
        "year": year,
        "trim": trim,
        "price": price,
        "mileage": mileage,
        "fuel_type": fuel_type,
        "transmission": transmission,
        "color": color,
        "body_type": body_type,
        "features": features,
        "status": status,
        "erp_status_raw": erp_status_raw,
        "isonline": isonline,
        "issold": issold,
        "isnewinstock": isnewinstock,
        "raw_payload": raw,
    }

    return vehicle_data, image_urls
