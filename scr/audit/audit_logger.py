import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


class LogLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class AuditLogger:
    name: str = "audit"
    log_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    _file_path: Path = field(init=False)
    _logger: logging.Logger = field(init=False, repr=False)

    _LOG_PATTERN = re.compile(r"^(?P<timestamp>[\d\-]+ [\d:,]+) \[(?P<level>[A-Z]+)\] (?P<message>.*)$")

    def __post_init__(self) -> None:
        target_dir = Path(self.log_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        self._file_path = target_dir / f"{self.name}.log"

        self._logger = logging.getLogger(f"audit.{self.name}")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

        if not self._logger.handlers:
            handler = logging.FileHandler(self._file_path, encoding="utf-8")
            formatter = logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    def info(self, message: str) -> None:
        self._logger.info(message)

    def warn(self, message: str) -> None:
        self._logger.warning(message)

    def error(self, message: str) -> None:
        self._logger.error(message)

    def get_logs(self, level: Optional[LogLevel] = None) -> List[str]:
        if not self._file_path.exists():
            return []

        target_level = level.value if level else None

        results: List[str] = []
        with open(self._file_path, mode="r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                match = self._LOG_PATTERN.match(line)
                if match:
                    log_level = match.group("level")
                    if target_level is None or log_level == target_level:
                        results.append(line)

        return results

audit_logger = AuditLogger()