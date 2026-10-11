"""Persiapan data aplikasi, terpisah dari presentasi desktop."""

from dataclasses import dataclass
import logging
from pathlib import Path

from benzie.persistence.database import initialize_database

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StartupState:
    database_path: Path
    schema_version: int


def initialize_application(data_directory: Path) -> StartupState:
    database_path = data_directory.expanduser().resolve() / "benzie.sqlite3"
    version = initialize_database(database_path)
    logger.info("Database lokal siap; versi skema %s", version)
    return StartupState(database_path=database_path, schema_version=version)
