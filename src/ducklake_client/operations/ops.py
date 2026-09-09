from .base import BaseDuckLakeOperation
from .schema_create import SchemaCreateOperation
from .table import TableOperation
from .view_list import ViewListOperation


class DuckLakeOperation(BaseDuckLakeOperation):
    """Base class for DuckLake operations."""

    @property
    def table(self) -> TableOperation:
        """Get a TableOperation instance for table operations."""
        return TableOperation(self.context)

    @property
    def schema_create(self) -> SchemaCreateOperation:
        """Get a SchemaCreateOperation instance for schema creation operations."""
        return SchemaCreateOperation(self.context)

    @property
    def view_list(self) -> ViewListOperation:
        """Get a ViewListOperation instance for view listing operations."""
        return ViewListOperation(self.context)
