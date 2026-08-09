from pathlib import Path

import click
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ALLOWED_FORMAT_VARIABLES = (
    "media_type",
    "media_format",
    "file",
    "file_extension",
    "file_name",
    "relative_path",
)


class GlobalSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CATALOGUER_")

    format_pattern: str | None = None
    unknown_format_pattern: str | None = None
    # validate_default is required for storage_location_must_exists to run when
    # the default is used. Validators skip defaults otherwise, so the directory
    # was never created unless CATALOGUER_STORAGE_LOCATION was set explicitly.
    storage_location: Path = Field(
        default=Path.home().joinpath(".catalogues/"), validate_default=True
    )

    @field_validator("format_pattern", "unknown_format_pattern")
    @classmethod
    def validate_format_pattern(cls, format_pattern: str | None):
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

    @field_validator("storage_location")
    @classmethod
    def storage_location_must_exists(cls, storage_location: Path):
        if storage_location:
            storage_location = storage_location.resolve()
            if storage_location.exists() and not storage_location.is_dir():
                raise ValueError(f"{storage_location} is not a directory")
            storage_location.mkdir(parents=True, exist_ok=True)
        return storage_location
