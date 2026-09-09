"""Public view helpers."""

from __future__ import annotations

from ducklake_client.modules.base import DuckLakeModule
from ducklake_client.operations import ViewListOperation
from ducklake_client.schema import ViewListing


class ViewModule(DuckLakeModule):
    """DuckLake view operations."""

    @property
    def ops(self) -> ViewListOperation:
        return ViewListOperation(self)

    def list(
        self,
        *,
        schema_name: str | None = None,
    ) -> list[ViewListing]:
        return self.ops.view_list(schema_name=schema_name)
