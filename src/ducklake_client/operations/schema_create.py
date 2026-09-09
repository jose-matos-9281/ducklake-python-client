"""Create DuckLake schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ducklake_client.exceptions import DuckLakeConfigError
from ducklake_client.utils import quote_identifier

from .base import BaseDuckLakeOperation

if TYPE_CHECKING:
    import duckdb


class SchemaCreateOperation(BaseDuckLakeOperation):
    """Create a DuckLake schema."""

    def create(
        self,
        name: str,
        *,
        if_not_exists: bool = True,
    ) -> duckdb.DuckDBPyConnection:
        if not name:
            raise DuckLakeConfigError("schema name must not be empty")
        if "." in name:
            raise DuckLakeConfigError("schema name must not include a catalog prefix")

        query = self.template("schema_create.sql").format(
            if_not_exists="IF NOT EXISTS " if if_not_exists else "",
            schema_name=".".join(
                quote_identifier(part) for part in (self.context.alias, name)
            ),
        )
        return self.context.connection.execute(query)
