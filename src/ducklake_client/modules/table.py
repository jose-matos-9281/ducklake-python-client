"""Public table helpers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ducklake_client.operations import TableOperation
from ducklake_client.schema import ColumnDef, TableInfo, TableListing

from .base import DuckLakeModule

if TYPE_CHECKING:
    import duckdb


class TableModule(DuckLakeModule):
    """DuckLake table operations."""

    @property
    def ops(self) -> TableOperation:
        """Get a TableOperation instance for table operations."""
        return TableOperation(self)

    def create(
        self,
        table_name: str,
        *,
        schema_name: str = "main",
        if_not_exists: bool = True,
        **columns: ColumnDef,
    ) -> duckdb.DuckDBPyConnection:
        return self.ops.create(
            table_name,
            schema_name,
        ).create(if_not_exists=if_not_exists, **columns)

    def create_from_file(
        self,
        name: str,
        source: str | Path,
        *,
        schema_name: str = "main",
        if_not_exists: bool = True,
    ) -> duckdb.DuckDBPyConnection:
        return self.ops.create(
            name,
            schema_name,
        ).create_from_file(
            source,
            if_not_exists=if_not_exists,
        )

    def add_column(
        self,
        name: str,
        column_name: str,
        column: ColumnDef,
        *,
        schema_name: str = "main",
        default_sql: str | None = None,
    ) -> duckdb.DuckDBPyConnection:
        return self.ops.alter(
            name,
            schema_name,
        ).add_column(
            column_name,
            column,
            default_sql=default_sql,
        )

    def drop_column(
        self,
        name: str,
        column_name: str,
        *,
        schema_name: str = "main",
    ) -> duckdb.DuckDBPyConnection:
        return self.ops.alter(
            name,
            schema_name,
        ).drop_column(column_name)

    def comment(
        self,
        name: str,
        comment: str | None,
        *,
        column_name: str | None = None,
        schema_name: str = "main",
    ) -> duckdb.DuckDBPyConnection:
        return self.ops.comment(
            name,
            schema_name,
        ).comment(
            comment,
            column_name=column_name,
        )

    def list(
        self,
        *,
        schema_name: str | None = None,
    ) -> list[TableListing]:
        return self.ops.list.table_list(schema_name=schema_name)

    def info(
        self,
        name: str,
        *,
        schema_name: str = "main",
        include_row_count: bool = True,
        include_snapshots: bool = True,
    ) -> TableInfo:
        return self.ops.info(
            name,
            schema_name=schema_name,
        ).info(
            include_row_count=include_row_count,
            include_snapshots=include_snapshots,
        )
