"""Comment on DuckLake tables and columns."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ducklake_client.exceptions import DuckLakeConfigError
from ducklake_client.utils import quote_identifier, quote_literal

from .base import BaseTableOperation

if TYPE_CHECKING:
    import duckdb


class TableCommentOperation(BaseTableOperation):
    """Base class for DuckLake table COMMENT operations."""

    def comment(
        self,
        comment: str | None,
        *,
        column_name: str | None = None,
    ) -> duckdb.DuckDBPyConnection:
        rendered_comment = self._comment_literal(comment)

        if column_name is None:
            query = self.template("table_comment.sql").format(
                table_name=self.qualified_table_name,
                comment=rendered_comment,
            )
        else:
            if not column_name:
                raise DuckLakeConfigError("column name must not be empty")
            query = self.template("table_column_comment.sql").format(
                column_name=f"{self.qualified_table_name}.{quote_identifier(column_name)}",
                comment=rendered_comment,
            )
        return self.context.connection.execute(query)

    def _comment_literal(self, comment: str | None) -> str:
        return "NULL" if comment is None else quote_literal(comment)
