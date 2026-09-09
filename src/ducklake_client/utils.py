from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

from ducklake_client.exceptions import DuckLakeConfigError


def quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def quote_literal(value: object) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _endpoint_host(endpoint: str) -> str:
    parsed = urlsplit(endpoint)
    if parsed.scheme and parsed.netloc:
        return urlunsplit(("", parsed.netloc, parsed.path, "", "")).removeprefix("//")
    return endpoint


def _format_secret_value(value: str | bool) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return quote_literal(value)


def _require_not_empty(name: str, value: object) -> None:
    if not str(value):
        raise DuckLakeConfigError(f"{name} must not be empty")


def _str_or_none(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _int_or_none(value: object) -> int | None:
    if value is None:
        return None
    # pyrefly: ignore [bad-argument-type]
    return int(value)


def _bool_or_none(value: object) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "t", "yes", "y"}
