from __future__ import annotations

from functools import cached_property

from ducklake_client.exceptions import DuckLakeConfigError
from ducklake_client.utils import quote_identifier

from ..base import BaseDuckLakeOperation, OperationContext


class BaseTableOperation(BaseDuckLakeOperation):
    """Base class for DuckLake table operations."""

    table_name: str
    schema_name: str

    def __init__(
        self,
        context: OperationContext,
        *,
        table_name: str,
        schema_name: str = "main",
    ) -> None:
        super().__init__(context)
        self.table_name = table_name
        self.schema_name = schema_name

    @cached_property
    def split_table_name(self) -> tuple[str, str]:
        if not self.table_name:
            raise DuckLakeConfigError("table name must not be empty")
        if not self.schema_name:
            raise DuckLakeConfigError("schema name must not be empty")

        parts = self.table_name.split(".")
        if len(parts) == 1:
            return self.schema_name, parts[0]
        if len(parts) == 2:
            if self.schema_name != "main":
                raise DuckLakeConfigError(
                    "pass either 'schema.table' or schema_name=, not both"
                )
            schema, table = parts
            if schema and table:
                return schema, table
        raise DuckLakeConfigError(f"invalid table name: {self.table_name!r}")

    @cached_property
    def qualified_table_name(self) -> str:
        return ".".join(
            quote_identifier(part)
            for part in (self.context.alias, self.schema_name, self.table_name)
        )
