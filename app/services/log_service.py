from pathlib import Path
from typing import List, Tuple

from app.core.config import settings


class LogService:
    @staticmethod
    def read_log_lines(*, skip: int = 0, limit: int = 100) -> Tuple[List[str], int]:
        log_path = Path(settings.LOG_FILE)
        if not log_path.is_file():
            return [], 0

        with open(log_path, encoding="utf-8", errors="replace") as log_file:
            lines = [line.rstrip("\n") for line in log_file.readlines()]

        lines.reverse()  # newest first
        total = len(lines)
        page = lines[skip : skip + limit]
        return page, total
