from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from ducklake_client.ports import StorageConfig
from ducklake_client.utils import _require_not_empty


@dataclass(frozen=True)
class DiskStorage(StorageConfig):
    """Local filesystem data storage."""

    PREFIX_ENV_VAR = "DUCKLAKE_STORAGE_DISK"
    path: str | Path

    def __post_init__(self) -> None:
        _require_not_empty("path", self.path)

    def data_path(self) -> str:
        return str(self.path)

    @classmethod
    def new(cls, env: Mapping[str, str]) -> Self:
        path = env.get(f"{cls.PREFIX_ENV_VAR}_PATH")
        if not path:
            raise ValueError(
                f"Missing required environment variable: {cls.PREFIX_ENV_VAR}_PATH"
            )
        return cls(path=path)
