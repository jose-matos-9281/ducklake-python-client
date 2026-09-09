from collections.abc import Mapping
from dataclasses import dataclass
from typing import Self

from ducklake_client.ports import CatalogConfig
from ducklake_client.utils import _require_not_empty


@dataclass(frozen=True)
class PostgresCatalog(CatalogConfig):
    """A DuckLake catalog stored in PostgreSQL."""

    PREFIX_ENV_VAR = "DUCKLAKE_CATALOG_POSTGRES"
    dsn: str
    opts: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        _require_not_empty("dsn", self.dsn)

    def attach_uri(self) -> str:
        return f"ducklake:postgres:{self.dsn}"

    def required_extensions(self) -> tuple[str, ...]:
        return ("postgres",)

    def attach_options(self) -> Mapping[str, object]:
        return self.opts or {}

    @classmethod
    def new(cls, env: Mapping[str, str]) -> Self:
        dsn = env.get(f"{cls.PREFIX_ENV_VAR}_DSN")
        if dsn is not None:
            return cls(dsn=dsn)
        host = env.get(f"{cls.PREFIX_ENV_VAR}_HOST")
        port = env.get(f"{cls.PREFIX_ENV_VAR}_PORT", 5432)
        user = env.get(f"{cls.PREFIX_ENV_VAR}_USER")
        password = env.get(f"{cls.PREFIX_ENV_VAR}_PASSWORD")
        database = env.get(f"{cls.PREFIX_ENV_VAR}_DATABASE")
        schema = env.get(f"{cls.PREFIX_ENV_VAR}_SCHEMA")
        if not any(v is not None for v in (host, port, user, password, database)):
            raise ValueError(
                f"Missing required environment variables for Postgres catalog: "
                f"{cls.PREFIX_ENV_VAR}_HOST, {cls.PREFIX_ENV_VAR}_PORT, "
                f"{cls.PREFIX_ENV_VAR}_USER, {cls.PREFIX_ENV_VAR}_PASSWORD, "
                f"{cls.PREFIX_ENV_VAR}_DATABASE, {cls.PREFIX_ENV_VAR}_SCHEMA"
                f" (or {cls.PREFIX_ENV_VAR}_DSN)"
            )
        dsn = (
            f"host={host} "
            f"port={port} "
            f"user={user} "
            f"password={password} "
            f"dbname={database} "
        )
        attach_options = {"METADATA_SCHEMA": schema} if schema else None

        return cls(dsn=dsn, opts=attach_options)
