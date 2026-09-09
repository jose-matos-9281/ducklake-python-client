"""Lazy DuckDB connection management for DuckLake."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, cast

from ducklake_client.exceptions import DuckLakeConnectionError
from ducklake_client.ports import CatalogConfig, StorageConfig

from ._attach import build_attach_sql
from .config import DuckDBConfig, _setting_sql

if TYPE_CHECKING:
    import duckdb

_SETTING_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass
class ConnectionManager:
    catalog: CatalogConfig
    storage: StorageConfig
    alias: str
    duckdb_config: DuckDBConfig = field(default_factory=DuckDBConfig)
    attach_options: Mapping[str, object] | None = None
    _connection: duckdb.DuckDBPyConnection | None = field(
        default=None, init=False, repr=False
    )

    def get(self) -> duckdb.DuckDBPyConnection:
        if self._connection is None:
            self._connection = self._connect()
        return self._connection

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def _connect(self) -> duckdb.DuckDBPyConnection:
        try:
            import duckdb

            config = cast(
                dict[str, str | bool | int | float | list[str]],
                dict(self.duckdb_config.config),
            )
            conn = (
                duckdb.connect(str(self.duckdb_config.database), config=config)
                if config
                else duckdb.connect(str(self.duckdb_config.database))
            )
            for name, value in self.duckdb_config.runtime_settings().items():
                conn.execute(_setting_sql(name, value))
            for extension in self._required_extensions():
                if self.duckdb_config.install_extensions:
                    conn.install_extension(extension)
                conn.load_extension(extension)
            for statement in self.storage.setup_statements(
                secret_name=f"{self.alias}_storage"
            ):
                conn.execute(statement)
            conn.execute(
                build_attach_sql(
                    catalog=self.catalog,
                    storage=self.storage,
                    alias=self.alias,
                    attach_options=self.attach_options,
                )
            )
            return conn
        except Exception as exc:
            raise DuckLakeConnectionError(
                "failed to initialize DuckLake connection"
            ) from exc

    def _required_extensions(self) -> tuple[str, ...]:
        names = [
            "ducklake",
            "parquet",
            *self.catalog.required_extensions(),
            *self.storage.required_extensions(),
            *self.duckdb_config.extensions,
        ]
        return tuple(dict.fromkeys(names))
