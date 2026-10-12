from typing import List
from sqlalchemy.orm import Session

from app.models.vehicle_image import VehicleImage


def get_vehicle_images(db: Session, vehicle_id: int) -> List[VehicleImage]:
    return (
        db.query(VehicleImage)
        .filter(VehicleImage.vehicle_id == vehicle_id)
        .order_by(VehicleImage.sort_order.asc(), VehicleImage.id.asc())
        .all()
    )


def replace_vehicle_images(
    db: Session, vehicle_id: int, image_urls: List[str]
) -> List[VehicleImage]:
    """
    Replace the image set for a vehicle with deduplicated URLs,
    setting the first image as primary and assigning sequential sort_order.
    """
    # Delete existing images for this vehicle
    db.query(VehicleImage).filter(VehicleImage.vehicle_id == vehicle_id).delete(
        synchronize_session=False
    )

    created_images: List[VehicleImage] = []
    seen_urls = set()
    order = 0

    for url in image_urls:
        clean_url = (url or "").strip()
        if not clean_url or clean_url in seen_urls:
            continue
        seen_urls.add(clean_url)
        img = VehicleImage(
            vehicle_id=vehicle_id,
            url=clean_url,
            is_primary=(order == 0),
            sort_order=order,
        )
        db.add(img)
        created_images.append(img)
        order += 1

    db.flush()
    return created_images
