"""Public DuckLake client entry point."""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager
from functools import cached_property
from typing import TYPE_CHECKING, Any, Self

from ducklake_client.exceptions import DuckLakeQueryError
from ducklake_client.modules import (
    SchemaModule,
    SnapshotsModule,
    TableModule,
    ViewModule,
)

from .base import DuckLakeConfig

if TYPE_CHECKING:
    import duckdb

logger = logging.getLogger(__name__)


class DuckLake:
    """A lazy DuckLake connection wrapper."""

    def __init__(self, config: DuckLakeConfig) -> None:
        self.alias = config.alias
        self._manager = config.get_connection_manager()

    @classmethod
    def new(cls, env: dict[str, str]) -> Self:
        """Create a new DuckLake from environment variables."""
        config = DuckLakeConfig.new(env)
        return cls(config)

    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        return self._manager.get()

    @cached_property
    def schema(self) -> SchemaModule:
        return SchemaModule(self)

    @cached_property
    def snapshots(self) -> SnapshotsModule:
        return SnapshotsModule(self)

    @cached_property
    def table(self) -> TableModule:
        return TableModule(self)

    @cached_property
    def view(self) -> ViewModule:
        return ViewModule(self)

    def sql_dicts(self, sql: str, **params: Any) -> list[dict[str, Any]]:
        """Run arbitrary SQL with named parameters and return rows as dicts.

        Named parameters use DuckDB's ``$name`` syntax. For no parameters, call
        with only ``sql``.
        """

        connection = self.connection
        if params:
            connection.execute(sql, params)
        else:
            connection.execute(sql)
        columns = [col[0] for col in (connection.description or [])]
        return [dict(zip(columns, row, strict=False)) for row in connection.fetchall()]

    def sql_scalar(self, sql: str, **params: Any) -> Any:
        """Run SQL with optional ``$name`` parameters and return a single scalar cell."""

        connection = self.connection
        try:
            if params:
                connection.execute(sql, params)
            else:
                connection.execute(sql)
            row = connection.fetchone()
        except DuckLakeQueryError:
            raise
        except Exception as exc:
            raise DuckLakeQueryError("DuckLake sql_scalar failed") from exc
        if row is None:
            raise DuckLakeQueryError("sql_scalar expected one row, got zero rows")
        if len(row) != 1:
            raise DuckLakeQueryError(
                f"sql_scalar expected exactly one column, got {len(row)}"
            )
        return row[0]

    def sql_one(self, sql: str, **params: Any) -> dict[str, Any]:
        """Run SQL with optional ``$name`` parameters and return exactly one row as a dict."""

        connection = self.connection
        try:
            if params:
                connection.execute(sql, params)
            else:
                connection.execute(sql)
            columns = [col[0] for col in (connection.description or [])]
            row = connection.fetchone()
        except DuckLakeQueryError:
            raise
        except Exception as exc:
            raise DuckLakeQueryError("DuckLake sql_one failed") from exc
        if row is None:
            raise DuckLakeQueryError("sql_one expected one row, got zero rows")
        if connection.fetchone() is not None:
            raise DuckLakeQueryError("sql_one expected one row, got multiple rows")
        return dict(zip(columns, row, strict=False))

    @contextmanager
    def transaction(self) -> Generator[Self, None, None]:
        """Run a block inside a DuckDB transaction on this lake's connection."""

        connection = self.connection
        connection.begin()
        try:
            yield self
        except BaseException:
            try:
                connection.rollback()
            except Exception:
                logger.exception("DuckLake transaction rollback failed")
            raise
        else:
            try:
                connection.commit()
            except Exception:
                try:
                    connection.rollback()
                except Exception:
                    logger.exception("DuckLake transaction rollback failed")
                raise

    def close(self) -> None:
        self._manager.close()

    def __enter__(self) -> Self:
        _ = self.connection
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()
