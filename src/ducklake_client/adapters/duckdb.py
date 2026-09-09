from collections.abc import Mapping
from typing import Self

from ducklake_client.duckdb import DuckDBConfig


class LocalDuckDBConfig(DuckDBConfig):
    """DuckDB connection and runtime settings for a local DuckLake client."""

    PREFIX_ENV_VAR = "DUCKLAKE_DUCKDB_LOCAL"

    @classmethod
    def new(cls, env: Mapping[str, str]) -> Self:
        database = env.get(f"{cls.PREFIX_ENV_VAR}_DATABASE", ":memory:")
        config = {}
        extensions = ()
        settings = {}
        install_extensions = True
        threads = None
        memory_limit = None
        max_temp_directory_size = None
        temp_directory = None
        s3_uploader_max_filesize = None

        return cls(
            database=database,
            config=config,
            extensions=extensions,
            settings=settings,
            install_extensions=install_extensions,
            threads=threads,
            memory_limit=memory_limit,
            max_temp_directory_size=max_temp_directory_size,
            temp_directory=temp_directory,
            s3_uploader_max_filesize=s3_uploader_max_filesize,
        )


class NoInternetDuckDBConfig(DuckDBConfig):
    """DuckDB connection and runtime settings for a local DuckLake client without internet access."""

    PREFIX_ENV_VAR = "DUCKLAKE_DUCKDB_NO_INTERNET"

    @classmethod
    def new(cls, env: Mapping[str, str]) -> Self:
        database = env.get(f"{cls.PREFIX_ENV_VAR}_DATABASE", ":memory:")
        extension_directory = env.get(f"{cls.PREFIX_ENV_VAR}_EXTENSION_DIRECTORY")
        extensions = env.get(
            f"{cls.PREFIX_ENV_VAR}_EXTENSIONS", "ducklake,parquet,postgres,azure"
        ).split(",")
        if not extension_directory:
            raise ValueError(
                f"Missing required environment variable: {cls.PREFIX_ENV_VAR}_EXTENSION_DIRECTORY"
            )
        config = {
            "extension_directory": extension_directory,
            "azure_transport_option_type": "curl",
        }
        extensions = tuple(ext.strip() for ext in extensions if ext.strip())
        settings = {}
        install_extensions = False
        threads = None
        memory_limit = None
        max_temp_directory_size = None
        temp_directory = None
        s3_uploader_max_filesize = None

        return cls(
            database=database,
            config=config,
            extensions=extensions,
            settings=settings,
            install_extensions=install_extensions,
            threads=threads,
            memory_limit=memory_limit,
            max_temp_directory_size=max_temp_directory_size,
            temp_directory=temp_directory,
            s3_uploader_max_filesize=s3_uploader_max_filesize,
        )
