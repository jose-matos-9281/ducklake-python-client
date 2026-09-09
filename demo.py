"""Create and query a local DuckLake table."""

from pathlib import Path
from tempfile import TemporaryDirectory

from ducklake_client import ColumnDef, DuckLake
from ducklake_client.adapters import DiskStorage, DuckDBCatalog, LocalDuckDBConfig
from ducklake_client.client import DuckLakeConfig


def main() -> None:
    with TemporaryDirectory(prefix="ducklake-demo-") as directory:
        root = Path(directory)
        config = DuckLakeConfig(
            catalog=DuckDBCatalog(root / "metadata.ducklake"),
            storage=DiskStorage(root / "data"),
            duckdb=LocalDuckDBConfig(),
        )

        with DuckLake(config) as lake:
            lake.schema.create("main")
            lake.table.create(
                "payments",
                id=ColumnDef("INTEGER", nullable=False),
                amount=ColumnDef("DECIMAL", nullable=False),
            )
            lake.connection.execute(
                "INSERT INTO lake.main.payments VALUES (?, ?), (?, ?)",
                [1, 25.50, 2, 99.99],
            )
            for payment in lake.sql_dicts(
                "SELECT id, amount FROM lake.main.payments ORDER BY id"
            ):
                print(payment)


if __name__ == "__main__":
    main()
