from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self, TypeAlias

from ducklake_client.exceptions import DuckLakeConfigError, DuckLakeConnectionError
from ducklake_client.utils import quote_literal

_SETTING_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


DuckDBConfigValue: TypeAlias = str | bool | int | float | list[str]
DuckDBSettingValue: TypeAlias = str | bool | int | float
DuckDBSettings: TypeAlias = Mapping[str, DuckDBSettingValue]


@dataclass(frozen=True)
class DuckDBConfig:
    """DuckDB connection and runtime settings for a DuckLake client."""

    database: str | Path = ":memory:"
    config: Mapping[str, DuckDBConfigValue] = field(default_factory=dict)
    extensions: tuple[str, ...] = ()
    settings: DuckDBSettings = field(default_factory=dict)
    install_extensions: bool = True
    threads: int | None = None
    memory_limit: str | None = None
    max_temp_directory_size: str | None = None
    temp_directory: str | Path | None = None
    s3_uploader_max_filesize: str | None = None

    def runtime_settings(self) -> dict[str, DuckDBSettingValue]:
        settings = dict(self.settings)
        explicit_settings: dict[str, DuckDBSettingValue] = {}
        if self.threads is not None:
            explicit_settings["threads"] = self.threads
        if self.memory_limit is not None:
            explicit_settings["memory_limit"] = self.memory_limit
        if self.max_temp_directory_size is not None:
            explicit_settings["max_temp_directory_size"] = self.max_temp_directory_size
        if self.temp_directory is not None:
            explicit_settings["temp_directory"] = str(self.temp_directory)
        if self.s3_uploader_max_filesize is not None:
            explicit_settings["s3_uploader_max_filesize"] = (
                self.s3_uploader_max_filesize
            )

        duplicates = set(settings).intersection(explicit_settings)
        if duplicates:
            names = ", ".join(sorted(duplicates))
            raise DuckLakeConfigError(
                f"DuckDB settings specified more than once: {names}"
            )
        settings.update(explicit_settings)
        return settings

    @classmethod
    def new(cls, env: Mapping[str, str]) -> Self:
        """Create a new DuckDBConfig from environment variables."""
        raise NotImplementedError(
            "DuckDBConfig.new() must be implemented by subclasses"
        )


def _setting_sql(name: str, value: DuckDBSettingValue) -> str:
    if not _SETTING_NAME.fullmatch(name):
        raise DuckLakeConnectionError(f"invalid DuckDB setting name: {name!r}")
    if isinstance(value, bool):
        rendered_value = "true" if value else "false"
    elif isinstance(value, int | float):
        rendered_value = str(value)
    else:
        rendered_value = quote_literal(value)
    return f"SET {name} = {rendered_value}"
