"""Workspace-local storage adapters for DuckLake.

DuckDB Azure reference used for this adapter:
- load/install the ``azure`` extension
- use ``az://`` or ``azure://`` paths for Blob Storage
- authenticate via ``CREATE SECRET (... TYPE azure ...)``

Example:
    AzureBlobStorage(
        container="ducklake",
        prefix="silver/payments",
        connection_string="DefaultEndpointsProtocol=https;...",
    )

    AzureBlobStorage(
        container="ducklake",
        prefix="silver/payments",
        account_name="mystorageaccount",
        provider="credential_chain",
        chain="cli;env",
    )
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal, Self, cast
from urllib.parse import urlsplit, urlunsplit

from ducklake_client.exceptions import DuckLakeConfigError
from ducklake_client.ports import StorageConfig

AzureProvider = Literal[
    "config", "credential_chain", "managed_identity", "service_principal"
]
AzureScheme = Literal["az", "azure"]


@dataclass(frozen=True)
class AzureStorage(StorageConfig):
    """Azure Blob Storage configuration for DuckLake data files.

    The adapter mirrors the shape of ``S3Storage`` while emitting DuckDB Azure
    secret statements and ``az://`` data paths.
    """

    PREFIX_ENV_VAR = "DUCKLAKE_STORAGE_AZURE"
    container: str
    prefix: str = ""
    account_name: str | None = None
    connection_string: str | None = None
    provider: AzureProvider = "config"
    chain: str | None = None
    tenant_id: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    client_certificate_path: str | None = None
    managed_identity_client_id: str | None = None
    managed_identity_object_id: str | None = None
    managed_identity_resource_id: str | None = None
    endpoint: str | None = None
    scheme: AzureScheme = "az"
    http_proxy: str | None = None
    proxy_user_name: str | None = None
    proxy_password: str | None = None
    scope: str | None = None
    extra_secret_options: Mapping[str, str | bool] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_not_empty("container", self.container)
        self._validate_auth_configuration()

    def data_path(self) -> str:
        suffix = f"/{self.prefix.lstrip('/')}" if self.prefix else ""
        if self.account_name:
            host = _fully_qualified_host(self.account_name, self.endpoint)
            return f"{self.scheme}://{host}/{self.container}{suffix}"
        return f"{self.scheme}://{self.container}{suffix}"

    def required_extensions(self) -> tuple[str, ...]:
        return ("azure",)

    def setup_statements(self, *, secret_name: str) -> tuple[str, ...]:
        options: dict[str, str | bool] = {}

        if self.connection_string:
            options["CONNECTION_STRING"] = self.connection_string
        else:
            options["PROVIDER"] = self.provider

        if self.account_name:
            options["ACCOUNT_NAME"] = self.account_name
        if self.chain:
            options["CHAIN"] = self.chain
        if self.tenant_id:
            options["TENANT_ID"] = self.tenant_id
        if self.client_id:
            options["CLIENT_ID"] = self.client_id
        if self.client_secret:
            options["CLIENT_SECRET"] = self.client_secret
        if self.client_certificate_path:
            options["CLIENT_CERTIFICATE_PATH"] = self.client_certificate_path
        if self.managed_identity_client_id:
            options["CLIENT_ID"] = self.managed_identity_client_id
        if self.managed_identity_object_id:
            options["OBJECT_ID"] = self.managed_identity_object_id
        if self.managed_identity_resource_id:
            options["RESOURCE_ID"] = self.managed_identity_resource_id
        if self.http_proxy:
            options["HTTP_PROXY"] = self.http_proxy
        if self.proxy_user_name:
            options["PROXY_USER_NAME"] = self.proxy_user_name
        if self.proxy_password:
            options["PROXY_PASSWORD"] = self.proxy_password
        if self.scope:
            options["SCOPE"] = self.scope

        for key, value in self.extra_secret_options.items():
            options[key.upper()] = value

        rendered_options = [
            "TYPE azure",
            *(f"{key} {_format_secret_value(value)}" for key, value in options.items()),
        ]
        rendered = ", ".join(rendered_options)
        return (
            f"CREATE OR REPLACE SECRET {quote_identifier(secret_name)} ({rendered})",
        )

    def _validate_auth_configuration(self) -> None:
        if self.connection_string and self.provider != "config":
            raise DuckLakeConfigError(
                "provider must stay 'config' when connection_string is supplied"
            )

        if self.chain and self.provider != "credential_chain":
            raise DuckLakeConfigError(
                "chain is only valid when provider='credential_chain'"
            )

        if not self.connection_string and not self.account_name:
            raise DuckLakeConfigError(
                "account_name is required unless connection_string is supplied"
            )

        if self.provider == "service_principal":
            if not self.tenant_id:
                raise DuckLakeConfigError("tenant_id is required for service_principal")
            if not self.client_id:
                raise DuckLakeConfigError("client_id is required for service_principal")
            if not (self.client_secret or self.client_certificate_path):
                raise DuckLakeConfigError(
                    "service_principal requires client_secret or client_certificate_path"
                )

        if self.provider != "service_principal" and any(
            value is not None
            for value in (
                self.tenant_id,
                self.client_id,
                self.client_secret,
                self.client_certificate_path,
            )
        ):
            raise DuckLakeConfigError(
                "tenant/client service principal fields require provider='service_principal'"
            )

        managed_identity_values = [
            self.managed_identity_client_id,
            self.managed_identity_object_id,
            self.managed_identity_resource_id,
        ]
        if self.provider != "managed_identity" and any(
            value is not None for value in managed_identity_values
        ):
            raise DuckLakeConfigError(
                "managed identity selectors require provider='managed_identity'"
            )

        if sum(value is not None for value in managed_identity_values) > 1:
            raise DuckLakeConfigError(
                "only one managed identity selector may be set: "
                "client_id, object_id, or resource_id"
            )

    @classmethod
    def new(cls, env: Mapping[str, str]) -> Self:
        container = env.get(f"{cls.PREFIX_ENV_VAR}_CONTAINER")
        if not container:
            raise ValueError(
                f"Missing required environment variable: {cls.PREFIX_ENV_VAR}_CONTAINER"
            )
        provider = env.get(f"{cls.PREFIX_ENV_VAR}_PROVIDER", "config")
        match provider:
            case "config":
                return cls(
                    container=container,
                    prefix=env.get(f"{cls.PREFIX_ENV_VAR}_PREFIX", ""),
                    account_name=env.get(f"{cls.PREFIX_ENV_VAR}_ACCOUNT_NAME"),
                    connection_string=env.get(
                        f"{cls.PREFIX_ENV_VAR}_CONNECTION_STRING"
                    ),
                    provider="config",
                    endpoint=env.get(f"{cls.PREFIX_ENV_VAR}_ENDPOINT"),
                    scheme=cast(
                        AzureScheme,
                        env.get(f"{cls.PREFIX_ENV_VAR}_SCHEME", "az"),
                    ),
                    http_proxy=env.get(f"{cls.PREFIX_ENV_VAR}_HTTP_PROXY"),
                    proxy_user_name=env.get(f"{cls.PREFIX_ENV_VAR}_PROXY_USER_NAME"),
                    proxy_password=env.get(f"{cls.PREFIX_ENV_VAR}_PROXY_PASSWORD"),
                    scope=env.get(f"{cls.PREFIX_ENV_VAR}_SCOPE"),
                )
            case "credential_chain":
                return cls(
                    container=container,
                    prefix=env.get(f"{cls.PREFIX_ENV_VAR}_PREFIX", ""),
                    account_name=env.get(f"{cls.PREFIX_ENV_VAR}_ACCOUNT_NAME"),
                    provider="credential_chain",
                    chain=env.get(f"{cls.PREFIX_ENV_VAR}_CHAIN"),
                    endpoint=env.get(f"{cls.PREFIX_ENV_VAR}_ENDPOINT"),
                    scheme=cast(
                        AzureScheme,
                        env.get(f"{cls.PREFIX_ENV_VAR}_SCHEME", "az"),
                    ),
                    http_proxy=env.get(f"{cls.PREFIX_ENV_VAR}_HTTP_PROXY"),
                    proxy_user_name=env.get(f"{cls.PREFIX_ENV_VAR}_PROXY_USER_NAME"),
                    proxy_password=env.get(f"{cls.PREFIX_ENV_VAR}_PROXY_PASSWORD"),
                    scope=env.get(f"{cls.PREFIX_ENV_VAR}_SCOPE"),
                )
            case "managed_identity":
                return cls(
                    container=container,
                    prefix=env.get(f"{cls.PREFIX_ENV_VAR}_PREFIX", ""),
                    account_name=env.get(f"{cls.PREFIX_ENV_VAR}_ACCOUNT_NAME"),
                    provider="managed_identity",
                    managed_identity_client_id=env.get(
                        f"{cls.PREFIX_ENV_VAR}_MANAGED_IDENTITY_CLIENT_ID"
                    ),
                    managed_identity_object_id=env.get(
                        f"{cls.PREFIX_ENV_VAR}_MANAGED_IDENTITY_OBJECT_ID"
                    ),
                    managed_identity_resource_id=env.get(
                        f"{cls.PREFIX_ENV_VAR}_MANAGED_IDENTITY_RESOURCE_ID"
                    ),
                    endpoint=env.get(f"{cls.PREFIX_ENV_VAR}_ENDPOINT"),
                    scheme=cast(
                        AzureScheme,
                        env.get(f"{cls.PREFIX_ENV_VAR}_SCHEME", "az"),
                    ),
                    http_proxy=env.get(f"{cls.PREFIX_ENV_VAR}_HTTP_PROXY"),
                    proxy_user_name=env.get(f"{cls.PREFIX_ENV_VAR}_PROXY_USER_NAME"),
                    proxy_password=env.get(f"{cls.PREFIX_ENV_VAR}_PROXY_PASSWORD"),
                    scope=env.get(f"{cls.PREFIX_ENV_VAR}_SCOPE"),
                )
            case "service_principal":
                return cls(
                    container=container,
                    prefix=env.get(f"{cls.PREFIX_ENV_VAR}_PREFIX", ""),
                    account_name=env.get(f"{cls.PREFIX_ENV_VAR}_ACCOUNT_NAME"),
                    provider="service_principal",
                    tenant_id=env.get(f"{cls.PREFIX_ENV_VAR}_TENANT_ID"),
                    client_id=env.get(f"{cls.PREFIX_ENV_VAR}_CLIENT_ID"),
                    client_secret=env.get(f"{cls.PREFIX_ENV_VAR}_CLIENT_SECRET"),
                    client_certificate_path=env.get(
                        f"{cls.PREFIX_ENV_VAR}_CLIENT_CERTIFICATE_PATH"
                    ),
                    endpoint=env.get(f"{cls.PREFIX_ENV_VAR}_ENDPOINT"),
                    scheme=cast(
                        AzureScheme,
                        env.get(f"{cls.PREFIX_ENV_VAR}_SCHEME", "az"),
                    ),
                    http_proxy=env.get(f"{cls.PREFIX_ENV_VAR}_HTTP_PROXY"),
                    proxy_user_name=env.get(f"{cls.PREFIX_ENV_VAR}_PROXY_USER_NAME"),
                    proxy_password=env.get(f"{cls.PREFIX_ENV_VAR}_PROXY_PASSWORD"),
                    scope=env.get(f"{cls.PREFIX_ENV_VAR}_SCOPE"),
                )
            case _:
                raise DuckLakeConfigError(f"Invalid provider: {provider}")


def quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _format_secret_value(value: str | bool) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return "'" + value.replace("'", "''") + "'"


def _fully_qualified_host(account_name: str, endpoint: str | None) -> str:
    host = _endpoint_host(endpoint or "blob.core.windows.net")
    if host.startswith(f"{account_name}."):
        return host
    return f"{account_name}.{host}"


def _endpoint_host(endpoint: str) -> str:
    parsed = urlsplit(endpoint)
    if parsed.scheme and parsed.netloc:
        return urlunsplit(("", parsed.netloc, parsed.path, "", "")).removeprefix("//")
    return endpoint


def _require_not_empty(name: str, value: object) -> None:
    if not str(value):
        raise DuckLakeConfigError(f"{name} must not be empty")
