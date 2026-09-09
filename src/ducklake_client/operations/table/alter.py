"""ALTER TABLE helpers for DuckLake-backed tables."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ducklake_client.exceptions import DuckLakeConfigError, DuckLakeQueryError
from ducklake_client.schema import ColumnDef
from ducklake_client.utils import quote_identifier

from .base import BaseTableOperation

if TYPE_CHECKING:
    import duckdb


class TableAlterOperation(BaseTableOperation):
    """Base class for DuckLake table ALTER operations."""

    def add_column(
        self,
        column_name: str,
        column: ColumnDef,
        *,
        default_sql: str | None = None,
    ) -> duckdb.DuckDBPyConnection:
        """Append a column via ``ALTER TABLE ... ADD COLUMN``."""

        if not column_name:
            raise DuckLakeConfigError("column_name must not be empty")
        if not isinstance(column, ColumnDef):
            raise TypeError(f"column must be a ColumnDef, got {type(column).__name__}")

        fragment = column.sql(column_name)
        suffix = f" DEFAULT {default_sql}" if default_sql else ""
        query = f"ALTER TABLE {self.qualified_table_name} ADD COLUMN {fragment}{suffix}"
        try:
            return self.context.connection.execute(query)
        except Exception as exc:
            raise DuckLakeQueryError("DuckLake table.add_column failed") from exc

    def drop_column(self, column_name: str) -> duckdb.DuckDBPyConnection:
        """Remove a column via ``ALTER TABLE ... DROP COLUMN``."""
        query = f"ALTER TABLE {self.qualified_table_name} DROP COLUMN {quote_identifier(column_name)}"
        try:
            return self.context.connection.execute(query)
        except Exception as exc:
            raise DuckLakeQueryError("DuckLake table.drop_column failed") from exc
