"""Collect DuckLake table metadata."""

from __future__ import annotations

from functools import cached_property
from typing import Any

from ducklake_client.exceptions import DuckLakeConfigError
from ducklake_client.schema import (
    DuckLakeTableMetadata,
    TableColumnSummary,
    TableInfo,
    TableInfoColumn,
    TablePartitionSpec,
    TableSnapshotInfo,
    TableSortSpec,
)
from ducklake_client.utils import (
    _bool_or_none,
    _int_or_none,
    _str_or_none,
    quote_identifier,
)

from .base import BaseTableOperation


class TableInfoOperation(BaseTableOperation):
    @cached_property
    def parameters(self) -> dict[str, object]:
        schema, table = self.split_table_name
        return {"catalog": self.context.alias, "schema": schema, "table": table}

    @cached_property
    def _schema_table_parameters(self) -> dict[str, object]:
        schema, table = self.split_table_name
        return {"schema": schema, "table": table}

    def info(
        self,
        *,
        include_row_count: bool = True,
        include_snapshots: bool = True,
    ) -> TableInfo:

        schema, table = self.split_table_name
        table_record = self._require_table()
        duckdb_table_record = self._duckdb_table_record()
        duckdb_column_comments = self._duckdb_column_comments()
        summary_by_name = self._summary_by_column()
        row_count = self._row_count() if include_row_count else None

        columns = [
            self._column_info(
                row,
                duckdb_column_comments.get(str(row["column_name"]), {}),
                summary_by_name,
            )
            for row in self._information_schema_columns()
        ]

        return TableInfo(
            catalog_name=self.context.alias,
            schema_name=schema,
            table_name=table,
            qualified_name=self.qualified_table_name,
            table_type=str(table_record["table_type"]),
            columns=columns,
            row_count=row_count,
            estimated_size=_int_or_none(duckdb_table_record.get("estimated_size"))
            if duckdb_table_record
            else None,
            table_comment=_str_or_none(duckdb_table_record.get("comment"))
            if duckdb_table_record
            else None,
            partition_specs=self._partition_specs(),
            sort_specs=self._sort_specs(),
            ducklake_metadata=self._ducklake_metadata(),
            snapshots=self._snapshots() if include_snapshots else [],
        )

    def _require_table(self) -> dict[str, Any]:
        result = self.rows(
            self.template("table_info_table.sql"),
            self.parameters,
            operation="table.info",
        )
        if not result:
            qualified = f"{self.parameters['schema']}.{self.parameters['table']}"
            raise DuckLakeConfigError(f"table not found: {qualified}")
        return result[0]

    def _duckdb_table_record(self) -> dict[str, Any]:
        result = self.optional_rows(
            self.template("table_info_duckdb_table.sql"),
            self.parameters,
            operation="table.info",
        )
        return result[0] if result else {}

    def _information_schema_columns(self) -> list[dict[str, Any]]:
        return self.rows(
            self.template("table_info_columns.sql"),
            self.parameters,
            operation="table.info",
        )

    def _duckdb_column_comments(self) -> dict[str, dict[str, Any]]:
        result = self.optional_rows(
            self.template("table_info_duckdb_columns.sql"),
            self.parameters,
            operation="table.info",
        )
        return {
            str(row["column_name"]): row
            for row in result
            if row.get("column_name") is not None
        }

    def _ducklake_metadata(self) -> DuckLakeTableMetadata | None:

        result = self.optional_rows(
            self.template("table_info_ducklake_metadata.sql"),
            self._schema_table_parameters,
            operation="table.info",
        )
        if not result:
            return None
        row = result[0]
        return DuckLakeTableMetadata(
            table_id=_int_or_none(row.get("table_id")),
            table_uuid=_str_or_none(row.get("table_uuid")),
            schema_id=_int_or_none(row.get("schema_id")),
            begin_snapshot=_int_or_none(row.get("begin_snapshot")),
            end_snapshot=_int_or_none(row.get("end_snapshot")),
            path=_str_or_none(row.get("path")),
            path_is_relative=_bool_or_none(row.get("path_is_relative")),
            record_count=_int_or_none(row.get("record_count")),
            next_row_id=_int_or_none(row.get("next_row_id")),
            file_size_bytes=_int_or_none(row.get("file_size_bytes")),
        )

    def _summary_by_column(self) -> dict[str, TableColumnSummary]:
        result = self.optional_rows(
            self.template("table_info_summary.sql").format(
                table_name=self.qualified_table_name
            ),
            operation="table.info",
        )
        summary: dict[str, TableColumnSummary] = {}
        for row in result:
            name = row.get("column_name")
            if name is not None:
                summary[str(name)] = self._column_summary(row)
        return summary

    def _row_count(self) -> int | None:
        result = self.optional_rows(
            self.template("table_info_row_count.sql").format(
                table_name=self.qualified_table_name
            ),
            operation="table.info",
        )
        if not result:
            return None
        return _int_or_none(result[0].get("row_count"))

    def _column_info(
        self,
        row: dict[str, Any],
        duckdb_column: dict[str, Any],
        summary_by_name: dict[str, TableColumnSummary],
    ) -> TableInfoColumn:
        name = str(row["column_name"])
        summary = summary_by_name.get(name)
        return TableInfoColumn(
            name=name,
            data_type=str(row["data_type"]),
            nullable=str(row["is_nullable"]).upper() == "YES",
            ordinal_position=int(row["ordinal_position"]),
            default=_str_or_none(row.get("column_default")),
            comment=_str_or_none(duckdb_column.get("comment")),
            summary=summary,
        )

    def _column_summary(self, row: dict[str, Any]) -> TableColumnSummary:
        return TableColumnSummary(
            min=_str_or_none(row.get("min")),
            max=_str_or_none(row.get("max")),
            approx_unique=_str_or_none(row.get("approx_unique")),
            avg=_str_or_none(row.get("avg")),
            std=_str_or_none(row.get("std")),
            q25=_str_or_none(row.get("q25")),
            q50=_str_or_none(row.get("q50")),
            q75=_str_or_none(row.get("q75")),
            count=_str_or_none(row.get("count")),
            null_percentage=_str_or_none(row.get("null_percentage")),
        )

    def _partition_specs(self) -> list[TablePartitionSpec]:
        return [
            TablePartitionSpec(
                partition_id=_int_or_none(row.get("partition_id")),
                partition_key_index=_int_or_none(row.get("partition_key_index")),
                column_id=_int_or_none(row.get("column_id")),
                column_name=_str_or_none(row.get("column_name")),
                transform=_str_or_none(row.get("transform")),
            )
            for row in self.optional_rows(
                self.template("table_info_partition_specs.sql"),
                self._schema_table_parameters,
                operation="table.info",
            )
        ]

    def _sort_specs(self) -> list[TableSortSpec]:
        return [
            TableSortSpec(
                sort_id=_int_or_none(row.get("sort_id")),
                sort_key_index=_int_or_none(row.get("sort_key_index")),
                expression=_str_or_none(row.get("expression")),
                dialect=_str_or_none(row.get("dialect")),
                sort_direction=_str_or_none(row.get("sort_direction")),
                null_order=_str_or_none(row.get("null_order")),
            )
            for row in self.optional_rows(
                self.template("table_info_sort_specs.sql"),
                self._schema_table_parameters,
                operation="table.info",
            )
        ]

    def _snapshots(
        self,
    ) -> list[TableSnapshotInfo]:
        result = self.optional_rows(
            self.template("table_info_snapshots.sql").format(
                snapshots_function=f"{quote_identifier(self.context.alias)}.snapshots()"
            ),
            operation="table.info",
        )
        return [
            TableSnapshotInfo(
                snapshot_id=int(row["snapshot_id"]),
                snapshot_time=row.get("snapshot_time"),
                schema_version=_int_or_none(row.get("schema_version")),
                next_catalog_id=_int_or_none(row.get("next_catalog_id")),
                next_file_id=_int_or_none(row.get("next_file_id")),
                changes_made=_str_or_none(row.get("changes_made")),
                author=_str_or_none(row.get("author")),
                commit_message=_str_or_none(row.get("commit_message")),
                commit_extra_info=_str_or_none(row.get("commit_extra_info")),
            )
            for row in result
            if row.get("snapshot_id") is not None
        ]
