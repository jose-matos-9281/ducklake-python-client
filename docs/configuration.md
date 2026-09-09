# Configuration model

`DuckLakeConfig` combines a catalog adapter, storage adapter, alias, DuckDB
profile, and optional `ATTACH` options. Adapters are imported from
`ducklake_client.adapters`; base contracts live in `ducklake_client.ports`.

## Constructor shape

```python
DuckLakeConfig(
    catalog=...,          # required CatalogConfig implementation
    storage=...,          # required StorageConfig implementation
    alias="lake",         # optional attached database name
    duckdb=...,           # optional DuckDBConfig implementation
    attach_options=None,
)
```

## Local configuration

```python
from ducklake_client.adapters import DiskStorage, DuckDBCatalog, LocalDuckDBConfig
from ducklake_client.client import DuckLakeConfig

config = DuckLakeConfig(
    catalog=DuckDBCatalog("metadata.ducklake"),
    storage=DiskStorage("data"),
    duckdb=LocalDuckDBConfig(),
)
```

## Available adapters

| Area | Adapters | Purpose |
|------|----------|---------|
| Catalog | `DuckDBCatalog`, `SqliteCatalog`, `PostgresCatalog` | Defines where DuckLake metadata lives |
| Storage | `DiskStorage`, `S3Storage`, `AzureStorage` | Defines where DuckLake data files live |
| DuckDB | `LocalDuckDBConfig`, `NoInternetDuckDBConfig` | Defines local connection and extension behavior |

`LocalDuckDBConfig` is the regular profile. `NoInternetDuckDBConfig` requires
an extension directory and disables extension installation, which is suitable
for an environment with preinstalled extensions.

## Environment configuration

Use `DuckLake.new(env)` when the deployment environment owns configuration:

```python
import os

from ducklake_client import DuckLake

lake = DuckLake.new(os.environ)
```

The selector variables are:

| Variable | Values | Default |
|----------|--------|---------|
| `DUCKLAKE_CATALOG_TYPE` | `duckdb`, `postgres`, `sqlite` | `duckdb` |
| `DUCKLAKE_STORAGE_TYPE` | `disk`, `s3`, `azure` | `disk` |
| `DUCKLAKE_DUCKDB_TYPE` | `local`, `no_internet` | `local` |
| `DUCKLAKE_ALIAS` | Attached catalog alias | `lake` |

Each selected adapter reads variables under its own prefix, for example
`DUCKLAKE_CATALOG_DUCKDB_PATH` and `DUCKLAKE_STORAGE_DISK_PATH`.

## Runtime settings

`DuckDBConfig` supports database, DuckDB connection config, additional
extensions, generic settings, and dedicated convenience fields such as
`threads`, `memory_limit`, and `temp_directory`. Supplying the same setting both
through `settings` and a dedicated field raises `DuckLakeConfigError`.

## Alias and attach options

`alias` is the DuckDB database name used after attachment. With the default,
relations are addressed as `lake.main.items`. `attach_options` are merged after
the adapter options and `DATA_PATH`, so they can override earlier values.

## Next step

Read [architecture.md](./architecture.md) for the connection bootstrap flow.
