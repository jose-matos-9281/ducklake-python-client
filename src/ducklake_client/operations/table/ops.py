from __future__ import annotations

from .alter import TableAlterOperation
from .base import BaseDuckLakeOperation
from .comment import TableCommentOperation
from .create import TableCreateOperation
from .info import TableInfoOperation
from .list import TableListOperation


class TableOperation(BaseDuckLakeOperation):
    def alter(self, table_name: str, schema_name: str = "main") -> TableAlterOperation:

        return TableAlterOperation(
            self.context,
            table_name=table_name,
            schema_name=schema_name,
        )

    def comment(
        self, table_name: str, schema_name: str = "main"
    ) -> TableCommentOperation:
        return TableCommentOperation(
            self.context,
            table_name=table_name,
            schema_name=schema_name,
        )

    def create(
        self, table_name: str, schema_name: str = "main"
    ) -> TableCreateOperation:
        return TableCreateOperation(
            self.context,
            table_name=table_name,
            schema_name=schema_name,
        )

    @property
    def list(self) -> TableListOperation:
        return TableListOperation(self.context)

    def info(self, table_name: str, schema_name: str = "main") -> TableInfoOperation:
        return TableInfoOperation(
            self.context,
            table_name=table_name,
            schema_name=schema_name,
        )
