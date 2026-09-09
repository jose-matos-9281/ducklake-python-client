"""Public DuckLake client entry point."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Self

from ducklake_client.duckdb import ConnectionManager, DuckDBConfig
from ducklake_client.ports import CatalogConfig, StorageConfig

logger = logging.getLogger(__name__)


@dataclass
class DuckLakeConfig:
    catalog: CatalogConfig
    storage: StorageConfig
    alias: str = "lake"
    duckdb: DuckDBConfig | None = None
    attach_options: Mapping[str, object] | None = None

    PREFIX_ENV_VAR = "DUCKLAKE"

    def get_connection_manager(self) -> ConnectionManager:
        return ConnectionManager(
            catalog=self.catalog,
            storage=self.storage,
            alias=self.alias,
            duckdb_config=self.duckdb or DuckDBConfig(),
            attach_options=self.attach_options,
        )

    def __post_init__(self) -> None:

        if not isinstance(self.catalog, CatalogConfig):
            raise TypeError(
                "catalog must be a DuckDBCatalog, PostgresCatalog, or SqliteCatalog"
            )
        if not isinstance(self.storage, StorageConfig):
            raise TypeError("storage must be a DiskStorage or S3Storage")

    @classmethod
    def new(cls, env: Mapping[str, str]) -> Self:
        """Create a new DuckLakeConfig from environment variables."""
        catalog_type = env.get(f"{cls.PREFIX_ENV_VAR}_CATALOG_TYPE", "duckdb")
        match catalog_type:
            case "duckdb":
                from ducklake_client.adapters import DuckDBCatalog

                catalog = DuckDBCatalog.new(env)
            case "postgres":
                from ducklake_client.adapters import PostgresCatalog

                catalog = PostgresCatalog.new(env)
            case "sqlite":
                from ducklake_client.adapters import SqliteCatalog

                catalog = SqliteCatalog.new(env)
            case _:
                raise ValueError(
                    f"Invalid catalog type: {catalog_type}. Must be one of: duckdb, postgres, sqlite"
                )

        storage_type = env.get(f"{cls.PREFIX_ENV_VAR}_STORAGE_TYPE", "disk")
        match storage_type:
            case "disk":
                from ducklake_client.adapters import DiskStorage

                storage = DiskStorage.new(env)
            case "s3":
                from ducklake_client.adapters import S3Storage

                storage = S3Storage.new(env)
            case "azure":
                from ducklake_client.adapters import AzureStorage

                storage = AzureStorage.new(env)
            case _:
                raise ValueError(
                    f"Invalid storage type: {storage_type}. Must be one of: disk, s3, azure"
                )

        duckdb_type = env.get(f"{cls.PREFIX_ENV_VAR}_DUCKDB_TYPE", "local")
        match duckdb_type:
            case "local":
                from ducklake_client.adapters import LocalDuckDBConfig

                duckdb = LocalDuckDBConfig.new(env)
            case "no_internet":
                from ducklake_client.adapters import NoInternetDuckDBConfig

                duckdb = NoInternetDuckDBConfig.new(env)
            case _:
                raise ValueError(
                    f"Invalid DuckDB type: {duckdb_type}. Must be one of: local, no_internet"
                )
        options: dict[str, object] = {}
        for key in env:
            if key.startswith(f"{cls.PREFIX_ENV_VAR}_ATTACH_OPTION_"):
                options[key] = env[key]

        return cls(
            catalog=catalog,
            storage=storage,
            alias=env.get(f"{cls.PREFIX_ENV_VAR}_ALIAS", "lake"),
            duckdb=duckdb,
            attach_options=options,
        )
