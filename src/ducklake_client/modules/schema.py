"""Public schema helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ducklake_client.operations import SchemaCreateOperation

from .base import DuckLakeModule

if TYPE_CHECKING:
    import duckdb


class SchemaModule(DuckLakeModule):
    """DuckLake schema operations."""

    @property
    def ops(self) -> SchemaCreateOperation:
        """Get a SchemaCreateOperation instance for schema creation operations."""
        return SchemaCreateOperation(self)

    def create(
        self,
        name: str,
        *,
        if_not_exists: bool = True,
    ) -> duckdb.DuckDBPyConnection:
        return self.ops.create(name, if_not_exists=if_not_exists)
