# Architecture and internals

The client separates configuration contracts, concrete infrastructure adapters,
connection management, and public modules.

## High-level flow

```text
DuckLakeConfig
  -> CatalogConfig + StorageConfig + DuckDBConfig
  -> ConnectionManager
       -> duckdb.connect(...)
       -> SET runtime settings
       -> install/load extensions
       -> run storage setup statements
       -> ATTACH DuckLake catalog AS <alias>
  -> SchemaModule / TableModule / ViewModule / SnapshotsModule
       -> focused operations and SQL templates
```

## Responsibilities

| Layer | Files | Responsibility |
|------|-------|----------------|
| Client | `client/` | `DuckLake`, lifecycle, query helpers, and `DuckLakeConfig` |
| Contracts | `ports.py` | Catalog and storage configuration interfaces |
| Adapters | `adapters/` | DuckDB, SQLite, PostgreSQL, local disk, S3, Azure, and DuckDB profiles |
| Connection bootstrap | `duckdb/` | Creates the DuckDB connection, loads extensions, and renders `ATTACH` SQL |
| Public modules | `modules/` | Feature-oriented consumer API |
| Operations | `operations/` | Focused implementations and result mapping |
| Data contracts | `schema.py` | Shared input and result types |

## Connection initialization order

`ConnectionManager` opens the connection lazily and uses this order:

1. Open DuckDB.
2. Apply runtime `SET` statements.
3. Install and load required extensions.
4. Run storage setup statements.
5. Attach the DuckLake catalog.

Required extensions include `ducklake` and `parquet`, plus extensions requested
by the selected catalog, storage, and DuckDB configuration. Duplicates are
removed while preserving their first appearance.

## Query boundaries

Use `lake.connection` for the native DuckDB API. The module helpers provide
typed, focused operations such as `lake.table.list()` and
`lake.table.info()`. The top-level helpers `sql_dicts`, `sql_one`, and
`sql_scalar` return Python-friendly results.

## Next step

Read [modules.md](./modules.md) for the consumer-facing API.
