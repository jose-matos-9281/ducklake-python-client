"""Create DuckLake tables."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ducklake_client.exceptions import DuckLakeConfigError
from ducklake_client.schema import ColumnDef
from ducklake_client.utils import quote_literal

from .base import BaseTableOperation

if TYPE_CHECKING:
    import duckdb


class TableCreateOperation(BaseTableOperation):
    def create(
        self,
        *,
        if_not_exists: bool = True,
        **columns: ColumnDef,
    ) -> duckdb.DuckDBPyConnection:
        if not columns:
            raise DuckLakeConfigError("table.create requires at least one column")
        for column_name, column in columns.items():
            if not isinstance(column, ColumnDef):
                raise TypeError(f"column {column_name!r} must be a ColumnDef")

        query = self.template("table_create.sql").format(
            if_not_exists="IF NOT EXISTS " if if_not_exists else "",
            table_name=self.qualified_table_name,
            columns=",\n    ".join(
                column.sql(column_name) for column_name, column in columns.items()
            ),
        )
        return self.context.connection.execute(query)

    def create_from_file(
        self,
        source: str | Path,
        *,
        if_not_exists: bool = True,
    ) -> duckdb.DuckDBPyConnection:
        if not str(source):
            raise DuckLakeConfigError("File source must not be empty")

        query = self.template("table_create_from_file.sql").format(
            if_not_exists="IF NOT EXISTS " if if_not_exists else "",
            table_name=self.qualified_table_name,
            source=quote_literal(source),
        )
        return self.context.connection.execute(query)
