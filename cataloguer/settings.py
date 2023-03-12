from pathlib import Path
from typing import Optional

import click
from pydantic import BaseSettings, validator


ALLOWED_FORMAT_VARIABLES = (
    "media_type",
    "media_format",
    "file",
    "file_extension",
    "file_name",
    "relative_path",
)


class GlobalSettings(BaseSettings):
    format_pattern: Optional[str] = None
    unknown_format_pattern: Optional[str] = None
    storage_location: Path = Path.home().joinpath(".catalogues/")

    class Config:
        env_prefix = "CATALOGUER_"

    @validator("format_pattern", "unknown_format_pattern", allow_reuse=True)
    def validate_format_pattern(cls, format_pattern: str):
        if format_pattern:
            try:
                format_pattern.format(
                    **{field: "" for field in ALLOWED_FORMAT_VARIABLES}
                )
            except KeyError as exception:
                raise click.BadParameter(
                    f'Unrecognised "{exception.args[0]}" format variable. Please check your format pattern.'
                )
        return format_pattern

    @validator("storage_location")
    def storage_location_must_exists(cls, storage_location: Path):
        if storage_location:
            storage_location = storage_location.resolve()
            if storage_location.exists() and not storage_location.is_dir():
                raise ValueError(f"{storage_location} is not a directory")
            storage_location.mkdir(parents=True, exist_ok=True)
        return storage_location
