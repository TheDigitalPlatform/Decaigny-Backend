import logging
from typing import Any, Dict, Optional, Set
from sqlalchemy.orm import Session

from app.crud import crud_vehicle, crud_vehicle_image, crud_vehicle_sync
from app.services.vehicle_mapper import map_ydd_vehicle
from app.services.ydd_client import YDDClient, YDDClientError, ydd_client

logger = logging.getLogger(__name__)


class VehicleSyncService:
    """
    Coordinates stock synchronization between Your Daily Drive (YDD) ERP
    and the Decaigny database.
    """

    def __init__(self, client: Optional[YDDClient] = None):
        self.client = client or ydd_client

    def check_health(self) -> Dict[str, Any]:
        """
        Check connectivity to YDD via /me and optionally /stats.
        """
        me_info = self.client.health_check()
        stats_info: Optional[Dict[str, Any]] = None
        try:
            stats_info = self.client.get_stats()
        except Exception as exc:
            logger.warning("Could not fetch YDD stats during health check: %s", exc)

        return {
            "status": "healthy",
            "me": me_info,
            "stats": stats_info,
        }

    def sync_inventory(
        self,
        db: Session,
        source: str = "n8n",
        mark_missing_as_sold: bool = True,
        filter_param: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute full stock sync:
        1. Create vehicle_syncs log (running)
        2. Fetch all cars from YDD
        3. Upsert vehicles and sync image URLs
        4. Detect new vehicles (is_new_to_us=True)
        5. Detect sold vehicles (explicit YDD flag or implicit missing from full sync)
        6. Record completion & counts
        """
        sync_run = crud_vehicle_sync.create_running(
            db,
            source=source,
            meta={"mark_missing_as_sold": mark_missing_as_sold, "filter": filter_param},
        )

        fetched_count = 0
        created_count = 0
        updated_count = 0
        sold_count = 0
        skipped_count = 0
        seen_erp_ids: Set[str] = set()

        try:
            logger.info("Starting vehicle inventory pull (sync_id=%s, source=%s)", sync_run.id, source)
            raw_cars = self.client.list_all_cars(filter_param=filter_param)
            fetched_count = len(raw_cars)
            logger.info("YDD returned %s cars to process", fetched_count)

            for raw in raw_cars:
                mapped = map_ydd_vehicle(raw)
                if not mapped:
                    skipped_count += 1
                    continue

                vehicle_data, image_urls = mapped
                erp_id = vehicle_data["erp_id"]
                seen_erp_ids.add(erp_id)

                vehicle, is_created, is_marked_sold = crud_vehicle.upsert_vehicle(db, vehicle_data)
                if is_created:
                    created_count += 1
                else:
                    updated_count += 1

                if is_marked_sold:
                    sold_count += 1

                # Sync image URLs
                crud_vehicle_image.replace_vehicle_images(db, vehicle.id, image_urls)

            # Detect implicit sold vehicles: available vehicles missing from full sync
            if mark_missing_as_sold and not filter_param and seen_erp_ids:
                implicit_sold = crud_vehicle.mark_missing_as_sold(db, seen_erp_ids)
                sold_count += implicit_sold
                logger.info("Marked %s missing vehicles as sold", implicit_sold)

            # Commit all changes to DB
            db.commit()

            crud_vehicle_sync.finish_success(
                db,
                sync_obj=sync_run,
                fetched_count=fetched_count,
                created_count=created_count,
                updated_count=updated_count,
                sold_count=sold_count,
                skipped_count=skipped_count,
            )

            logger.info(
                "Vehicle sync completed successfully | id=%s, fetched=%s, created=%s, updated=%s, sold=%s, skipped=%s",
                sync_run.id,
                fetched_count,
                created_count,
                updated_count,
                sold_count,
                skipped_count,
            )

            return {
                "sync_id": sync_run.id,
                "fetched": fetched_count,
                "created": created_count,
                "updated": updated_count,
                "sold": sold_count,
                "skipped": skipped_count,
            }

        except Exception as exc:
            db.rollback()
            logger.exception("Vehicle sync failed for run %s: %s", sync_run.id, exc)
            crud_vehicle_sync.finish_failed(
                db,
                sync_obj=sync_run,
                error_message=str(exc),
                fetched_count=fetched_count,
                created_count=created_count,
                updated_count=updated_count,
                sold_count=sold_count,
                skipped_count=skipped_count,
            )
            raise


vehicle_sync_service = VehicleSyncService()
