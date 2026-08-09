# Changelog

## [v3.0] - 2026-08-10

### Breaking Changes
* Minimum supported Python is now 3.10 (required by current Pillow, click and pytest releases)

### Features
* Upgraded to current dependencies: Pillow 12, pydantic 2, click 8.4, rich-click 1.9, python-dateutil 2.9
* Pillow 12 publishes prebuilt wheels for all supported Python versions, so installing no longer needs a
  C toolchain to build Pillow from source

### Bug Fixes
* **EXIF creation dates are read from the Exif sub-IFD again.** Metadata extraction used the private
  `Image._getexif()`, which returned the base IFD and the Exif sub-IFD already merged. The public
  `Image.getexif()` exposes only the base IFD, and `DateTimeOriginal` lives in the sub-IFD - so reading
  it naively loses capture dates silently, with files falling back to filename heuristics or
  `unknown_format_pattern` and no error raised. Both IFDs are now read explicitly.
* `storage_location` is now created when the default is used. The validator that creates the directory
  never ran on the default value, so a fresh install could fail with `FileNotFoundError` when saving a
  catalogue unless `CATALOGUER_STORAGE_LOCATION` was set explicitly.
* Fixed the `sort` command help text, which duplicated the description of `move`.

### Documentation
* Documented the `libmagic` system requirement, needed by `python-magic`
* Added the missing `sort` command to the command list in the README

### Internal
* Migrated to pydantic v2: `BaseSettings` now comes from `pydantic-settings`, `validator` ->
  `field_validator`, and `class Config` -> `ConfigDict`/`SettingsConfigDict`
* Added `tests/test_metadata.py` covering EXIF sub-IFD reads, base-IFD fallback, TIFF tags, images
  without EXIF, non-image files and path-based date detection. The EXIF path had no test coverage
  before, which is why the metadata regression was not caught by the suite

## [v2.2] - 2023-10-22
* Adding sort feature

## [v2.1] - 2023-03-12

### Features
* Duplication order now uses path length when file names have the same length
* Exposing format-pattern and unknown-format-pattern as CLI parameters

### Bug Fixes
* Fixed report when deleting duplicate files
* Ordering by file length too on the duplicate report given by the inspect command to make behaviour consistent


## [v2.0.1] - 2023-03-04
### Features

* breaking change - Complete rework of the application
