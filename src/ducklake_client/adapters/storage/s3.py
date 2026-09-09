from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Self

from ducklake_client.ports import StorageConfig
from ducklake_client.utils import (
    _endpoint_host,
    _format_secret_value,
    _require_not_empty,
    quote_identifier,
)


@dataclass(frozen=True)
class S3Storage(StorageConfig):
    """S3-compatible object storage for DuckLake data files."""

    PREFIX_ENV_VAR = "DUCKLAKE_STORAGE_S3"
    bucket: str
    prefix: str = ""
    endpoint: str | None = None
    region: str | None = None
    key_id: str | None = None
    secret_access_key: str | None = None
    session_token: str | None = None
    url_style: str | None = None
    use_ssl: bool | None = None
    extra_secret_options: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_not_empty("bucket", self.bucket)

    def data_path(self) -> str:
        suffix = f"/{self.prefix.lstrip('/')}" if self.prefix else ""
        return f"s3://{self.bucket}{suffix}"

    def required_extensions(self) -> tuple[str, ...]:
        return ("httpfs",)

    def setup_statements(self, *, secret_name: str) -> tuple[str, ...]:
        options: dict[str, str | bool] = {}
        if self.key_id:
            options["KEY_ID"] = self.key_id
        if self.secret_access_key:
            options["SECRET"] = self.secret_access_key
        if self.session_token:
            options["SESSION_TOKEN"] = self.session_token
        if self.region:
            options["REGION"] = self.region
        if self.endpoint:
            options["ENDPOINT"] = _endpoint_host(self.endpoint)
        if self.url_style:
            options["URL_STYLE"] = self.url_style
        if self.use_ssl is not None:
            options["USE_SSL"] = self.use_ssl
        for key, value in self.extra_secret_options.items():
            options[key.upper()] = value

        if not options:
            return ()

        rendered = ", ".join(
            [
                "TYPE s3",
                *(
                    f"{key} {_format_secret_value(value)}"
                    for key, value in options.items()
                ),
            ]
        )
        return (
            f"CREATE OR REPLACE SECRET {quote_identifier(secret_name)} ({rendered})",
        )

    @classmethod
    def new(cls, env: Mapping[str, str]) -> Self:
        bucket = env.get(f"{cls.PREFIX_ENV_VAR}_BUCKET")

        if not bucket:
            raise ValueError(
                f"Missing required environment variable: {cls.PREFIX_ENV_VAR}_BUCKET"
            )
        return cls(
            bucket=bucket,
            prefix=env.get(f"{cls.PREFIX_ENV_VAR}_PREFIX", ""),
            endpoint=env.get(f"{cls.PREFIX_ENV_VAR}_ENDPOINT"),
            region=env.get(f"{cls.PREFIX_ENV_VAR}_REGION"),
            key_id=env.get(f"{cls.PREFIX_ENV_VAR}_KEY_ID"),
            secret_access_key=env.get(f"{cls.PREFIX_ENV_VAR}_SECRET_ACCESS_KEY"),
            session_token=env.get(f"{cls.PREFIX_ENV_VAR}_SESSION_TOKEN"),
            url_style=env.get(f"{cls.PREFIX_ENV_VAR}_URL_STYLE"),
            use_ssl=env.get(f"{cls.PREFIX_ENV_VAR}_USE_SSL") == "true",
        )
