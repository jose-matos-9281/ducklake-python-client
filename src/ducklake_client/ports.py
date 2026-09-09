"""Typed configuration for DuckLake connections."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Self


class CatalogConfig:
    """Base class for DuckLake catalog configuration."""

    def attach_uri(self) -> str:
        raise NotImplementedError

    def attach_options(self) -> Mapping[str, object]:
        return {}

    def required_extensions(self) -> tuple[str, ...]:
        return ()

    @classmethod
    def new(cls, env: Mapping[str, str]) -> Self:
        raise NotImplementedError


class StorageConfig:
    """Base class for DuckLake data storage configuration."""

    def data_path(self) -> str:
        raise NotImplementedError

    def required_extensions(self) -> tuple[str, ...]:
        return ()

    def setup_statements(self, *, secret_name: str) -> tuple[str, ...]:
        return ()

    @classmethod
    def new(cls, env: Mapping[str, str]) -> Self:
        raise NotImplementedError
