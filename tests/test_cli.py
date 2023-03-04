import os
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from catalogue.cli import cli, Context, GlobalSettings, Storage

FIXTURES_PATH = (
    Path(os.path.dirname(os.path.realpath(__file__)))
    .joinpath("fixtures/test-files")
    .resolve(strict=True)
)


@pytest.fixture
def test_catalogue_path():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname).resolve(strict=True)


@pytest.fixture
def cli_runner(monkeypatch, storage_path):
    monkeypatch.setenv("CATALOGUE_STORAGE_LOCATION", str(storage_path))
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield runner


def invoke(args, runner):
    global_settings = GlobalSettings()
    context = Context(
        global_settings=global_settings,
        storage=Storage(path=global_settings.storage_location),
        workdir=Path.cwd(),
        verbose=False,
        interactive=False,
    )
    return runner.invoke(args=args, cli=cli, obj=context)


def test_inspect(cli_runner, test_catalogue_path):
    result = invoke(args=("inspect", str(test_catalogue_path)), runner=cli_runner)

    assert result.exit_code == 0, result.output


def test_create_catalogue_and_adding_files(
    monkeypatch, cli_runner, test_catalogue_path
):
    monkeypatch.setenv("CATALOGUE_FORMAT_PATTERN", "%Y/%m/%d/{file}")

    result = invoke(
        args=("create-catalogue", "test_catalogue", str(test_catalogue_path)),
        runner=cli_runner,
    )
    assert result.exit_code == 0, result.output

    # add some files to catalogue
    result = invoke(
        args=("copy", str(FIXTURES_PATH.joinpath("different_files")), "test_catalogue"),
        runner=cli_runner,
    )
    assert result.exit_code == 0, result.output
    assert "Detected 5 files" in result.stdout
    assert "5 files have not being processed" in result.stdout

    # add some files directly to the path (so catalogue settings do not apply)
    monkeypatch.setenv("CATALOGUE_FORMAT_PATTERN", "{file}")
    result = invoke(
        args=(
            "copy",
            str(FIXTURES_PATH.joinpath("different_files")),
            str(test_catalogue_path),
        ),
        runner=cli_runner,
    )
    assert result.exit_code == 0, result.output
    assert "Detected 5 files" in result.stdout
    assert "Copy 5 files" in result.stdout


def test_copy_files_without_duplicates(monkeypatch, cli_runner, test_catalogue_path):
    monkeypatch.setenv("CATALOGUE_FORMAT_PATTERN", "{file}")

    # Only one copy of the same file should be imported
    result = invoke(
        args=("copy", str(FIXTURES_PATH.joinpath("duplicates")), "."), runner=cli_runner
    )
    assert result.exit_code == 0, result.output
    assert "Detected 1 file" in result.stdout

    # Already present files should be skipped
    result = invoke(
        args=("copy", str(FIXTURES_PATH.joinpath("duplicates")), "."), runner=cli_runner
    )
    assert result.exit_code == 0, result.output
    assert "Detected 0 files" in result.stdout


def test_delete_duplicates(cli_runner, test_catalogue_path):
    # Only one copy of the same file should be imported
    result = invoke(
        args=(
            "delete-duplicates",
            str(FIXTURES_PATH.joinpath("duplicates")),
            "--dry-run",
        ),
        runner=cli_runner,
    )
    assert result.exit_code == 0, result.output
    assert "Detected 1 file" in result.stdout


def test_delete_duplicates_across_directories(cli_runner, test_catalogue_path):
    # Only one copy of the same file should be imported
    result = invoke(
        args=(
            "delete-duplicates",
            str(FIXTURES_PATH.joinpath("duplicates")),
            str(FIXTURES_PATH.joinpath("different_files")),
            "--dry-run",
        ),
        runner=cli_runner,
    )
    assert result.exit_code == 0, result.output
    assert "Detected 1 file" in result.stdout
