# Getting started with ducklake-python-client-fork

`ducklake-python-client-fork` opens a DuckLake catalog through DuckDB and provides typed
helpers for common catalog operations.

## Quick path

1. Build a `DuckLakeConfig` from one catalog adapter, one storage adapter, and an optional DuckDB profile.
2. Pass that config to `DuckLake`.
3. Use the client as a context manager, then work through its modules or native DuckDB connection.

## Minimal example

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
    rows = lake.sql_dicts("SELECT * FROM lake.main.items")
```

## Connection lifecycle

Construction does not open DuckDB. The connection is initialized when you access
`lake.connection`, call a module method, or enter the context manager.

The first access:

1. Opens DuckDB.
2. Applies runtime settings.
3. Installs and loads required extensions.
4. Runs storage setup statements when required.
5. Attaches the DuckLake catalog under `config.alias` (`lake` by default).

Use `with DuckLake(config) as lake:` whenever possible. Alternatively, call
`lake.close()` when the client is no longer needed.

## Common flows

### Load a table from a file

```python
with DuckLake(config) as lake:
    lake.table.create_from_file(
        "stations",
        "https://blobs.duckdb.org/nl_stations.csv",
    )
```

### Query data

Use `lake.connection` for the full DuckDB API:

```python
count = lake.connection.sql("SELECT count(*) FROM lake.main.items").fetchone()[0]
```

Use the convenience helpers for Python values:

```python
rows = lake.sql_dicts("SELECT $n AS value", n=41)
one = lake.sql_one("SELECT 42 AS answer")
value = lake.sql_scalar("SELECT count(*) FROM lake.main.items")
```

### Group changes in a transaction

```python
with DuckLake(config) as lake:
    with lake.transaction():
        lake.schema.create("main")
        lake.table.create("items", id=ColumnDef("INTEGER", nullable=False))
```

`transaction()` commits on success and rolls back when the block raises.

## Next step

Read [configuration.md](./configuration.md) to choose adapters and runtime settings.
