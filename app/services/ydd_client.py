import logging
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class YDDClientError(Exception):
    """Custom exception for YDD API client errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response_text: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class YDDClient:
    """
    HTTP client for Your Daily Drive (YDD) ERP API.
    Reads credentials exclusively from backend settings / .env.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        dealer_id: Optional[str] = None,
        api_key: Optional[str] = None,
        language: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.base_url = (base_url or settings.YDD_BASE_URL).strip().rstrip("/")
        self.dealer_id = (dealer_id or settings.YDD_DEALER_ID).strip()
        self.api_key = (api_key or settings.YDD_API_KEY).strip()
        self.language = language or settings.YDD_LANGUAGE or "nl"
        self.timeout = timeout or settings.YDD_TIMEOUT_SECONDS or 30

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-DEALER-ID": self.dealer_id,
            "Accept": "application/json",
        }

    def _validate_config(self) -> None:
        missing = [
            name
            for name, value in (
                ("YDD_BASE_URL", self.base_url),
                ("YDD_API_KEY", self.api_key),
                ("YDD_DEALER_ID", self.dealer_id),
            )
            if not value
        ]
        if missing:
            message = (
                f"YDD client is not configured: missing {', '.join(missing)}. "
                "Set them in .env and restart the server."
            )
            logger.error(message)
            raise YDDClientError(message)

    def _get_client(self) -> httpx.Client:
        self._validate_config()
        return httpx.Client(
            base_url=self.base_url,
            headers=self.headers,
            timeout=self.timeout,
        )

    def health_check(self) -> Dict[str, Any]:
        """
        Verify YDD connectivity via GET /me.
        """
        endpoint = "/me"
        url = f"{self.base_url}{endpoint}"
        logger.info("YDD health check calling: %s", url)
        try:
            with self._get_client() as client:
                response = client.get(endpoint)
                if response.status_code != 200:
                    logger.warning("YDD /me returned status %s: %s", response.status_code, response.text)
                    raise YDDClientError(
                        f"YDD health check failed with status {response.status_code}",
                        status_code=response.status_code,
                        response_text=response.text,
                    )
                return response.json()
        except httpx.RequestError as exc:
            logger.error("YDD health check request failed: %s", exc)
            raise YDDClientError(f"YDD connection error: {exc}") from exc

    def get_stats(self) -> Dict[str, Any]:
        """
        Retrieve stock health statistics via GET /stats.
        """
        endpoint = "/stats"
        logger.info("YDD getting stats via: %s%s", self.base_url, endpoint)
        try:
            with self._get_client() as client:
                response = client.get(endpoint)
                if response.status_code != 200:
                    logger.warning("YDD /stats returned status %s: %s", response.status_code, response.text)
                    raise YDDClientError(
                        f"YDD stats failed with status {response.status_code}",
                        status_code=response.status_code,
                        response_text=response.text,
                    )
                return response.json()
        except httpx.RequestError as exc:
            logger.error("YDD stats request failed: %s", exc)
            raise YDDClientError(f"YDD connection error: {exc}") from exc

    def list_cars(
        self,
        page: int = 1,
        filter_param: Optional[str] = None,
        filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch a single page of cars via GET /cars?language=&page=&filter=.
        """
        endpoint = "/cars"
        active_filter = filter if filter is not None else filter_param
        params: Dict[str, Any] = {
            "language": self.language,
            "page": page,
        }
        if active_filter:
            params["filter"] = active_filter

        logger.info("YDD fetching cars page %s with params %s", page, params)
        try:
            with self._get_client() as client:
                response = client.get(endpoint, params=params)
                if response.status_code != 200:
                    logger.error(
                        "YDD /cars failed with status %s: %s", response.status_code, response.text
                    )
                    raise YDDClientError(
                        f"YDD /cars error {response.status_code}: {response.text}",
                        status_code=response.status_code,
                        response_text=response.text,
                    )
                return response.json()
        except httpx.RequestError as exc:
            logger.error("YDD /cars connection error on page %s: %s", page, exc)
            raise YDDClientError(f"YDD connection error on page {page}: {exc}") from exc

    def get_car(self, car_id: str) -> Dict[str, Any]:
        """
        Fetch single car details via GET /car/?id=&language=.
        """
        endpoint = "/car/"
        params = {
            "id": car_id,
            "language": self.language,
        }
        try:
            with self._get_client() as client:
                response = client.get(endpoint, params=params)
                if response.status_code != 200:
                    raise YDDClientError(
                        f"YDD /car/ error {response.status_code}: {response.text}",
                        status_code=response.status_code,
                        response_text=response.text,
                    )
                return response.json()
        except httpx.RequestError as exc:
            logger.error("YDD /car/ connection error for id %s: %s", car_id, exc)
            raise YDDClientError(f"YDD connection error: {exc}") from exc

    def get_images(self, vin: Optional[str] = None, reference: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch car images via GET /car/images?vin=&reference=.
        """
        endpoint = "/car/images"
        params: Dict[str, str] = {}
        if vin:
            params["vin"] = vin
        if reference:
            params["reference"] = reference

        try:
            with self._get_client() as client:
                response = client.get(endpoint, params=params)
                if response.status_code != 200:
                    raise YDDClientError(
                        f"YDD /car/images error {response.status_code}: {response.text}",
                        status_code=response.status_code,
                        response_text=response.text,
                    )
                data = response.json()
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    return data.get("images") or data.get("data") or []
                return []
        except httpx.RequestError as exc:
            logger.error("YDD /car/images connection error: %s", exc)
            raise YDDClientError(f"YDD connection error: {exc}") from exc

    def list_all_cars(
        self,
        filter_param: Optional[str] = None,
        filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all cars by iterating over pages until page > maxpage.
        """
        active_filter = filter if filter is not None else filter_param
        all_cars: List[Dict[str, Any]] = []
        page = 1
        max_page = 1

        while page <= max_page:
            data = self.list_cars(page=page, filter=active_filter)

            # Extract cars list
            if isinstance(data, dict):
                cars_chunk = data.get("cars") or data.get("data") or []
                meta = data.get("meta") or {}
                if isinstance(meta, dict):
                    max_page = int(meta.get("maxpage") or meta.get("max_page") or meta.get("total_pages") or max_page)
            elif isinstance(data, list):
                cars_chunk = data
            else:
                cars_chunk = []

            if not cars_chunk:
                logger.info("YDD list_all_cars: no cars returned on page %s, stopping pagination", page)
                break

            all_cars.extend(cars_chunk)
            logger.info("YDD page %s/%s fetched (%s cars in batch, %s total)", page, max_page, len(cars_chunk), len(all_cars))
            page += 1

            # Safety guard against infinite loops
            if page > 500:
                logger.warning("Reached safety limit of 500 pages in YDD list_all_cars")
                break

        return all_cars


# Shared default singleton
ydd_client = YDDClient()
