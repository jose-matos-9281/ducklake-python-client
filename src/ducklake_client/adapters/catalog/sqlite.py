from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from ducklake_client.ports import CatalogConfig
from ducklake_client.utils import _require_not_empty


@dataclass(frozen=True)
class SqliteCatalog(CatalogConfig):
    """A DuckLake catalog stored in SQLite."""

    PREFIX_ENV_VAR = "DUCKLAKE_CATALOG_SQLITE"
    path: str | Path

    def __post_init__(self) -> None:
        _require_not_empty("path", self.path)

    def attach_uri(self) -> str:
        return f"ducklake:sqlite:{self.path}"

    def attach_options(self) -> Mapping[str, object]:
        return {
            "META_JOURNAL_MODE": "WAL",
            "META_BUSY_TIMEOUT": 5000,
        }

    def required_extensions(self) -> tuple[str, ...]:
        return ("sqlite",)

    @classmethod
    def new(cls, env: Mapping[str, str]) -> Self:
        path = env.get(f"{cls.PREFIX_ENV_VAR}_PATH")
        if not path:
            raise ValueError(
                f"Missing required environment variable: {cls.PREFIX_ENV_VAR}_PATH"
            )
        return cls(path=path)
