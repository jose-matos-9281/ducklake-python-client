# ducklake-python-client-fork

Lightweight Python helpers for opening DuckLake connections through DuckDB.

## Install

```bash
pip install ducklake-python-client-fork
```

## Quick start

```python
from ducklake_client import ColumnDef, DuckLake
from ducklake_client.adapters import DiskStorage, DuckDBCatalog, LocalDuckDBConfig
from ducklake_client.client import DuckLakeConfig

config = DuckLakeConfig(
    catalog=DuckDBCatalog("metadata.ducklake"),
    storage=DiskStorage("data"),
    duckdb=LocalDuckDBConfig(),
)

with DuckLake(config) as lake:
    lake.schema.create("main")
    lake.table.create(
        "items",
        id=ColumnDef("INTEGER", nullable=False),
        name=ColumnDef("VARCHAR"),
    )
    lake.connection.execute("INSERT INTO lake.main.items VALUES (?, ?)", [1, "example"])
    print(lake.sql_dicts("SELECT * FROM lake.main.items"))
```

`DuckLake` opens DuckDB lazily on first use. It installs and loads the required
extensions, attaches the catalog as `lake`, and exposes the native connection
through `lake.connection`.

Run `python demo.py` for a complete local example.

## Documentation

- [Getting started](docs/getting-started.md)
- [Configuration](docs/configuration.md)
- [Public modules](docs/modules.md)
- [Architecture](docs/architecture.md)
