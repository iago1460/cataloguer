import os
import tempfile
from datetime import timezone, datetime

from pathlib import Path
from cataloguer.filesystem.file import File
from cataloguer.filesystem.directory import Catalogue
import pytest


TEST_FILES_PATH = (
    Path(os.path.dirname(os.path.realpath(__file__)))
    .joinpath("test-files")
    .resolve(strict=True)
)

test_dir = os.path.dirname(os.path.realpath(__file__))

TEST_FILE_PATH = Path("tests/fixtures/test-files/text-file.txt").resolve()


@pytest.fixture
def text_file():
    text_file_path = TEST_FILES_PATH.joinpath("text-file.txt")
    assert text_file_path.exists()
    return File(text_file_path)


@pytest.fixture
def storage_path():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname).resolve(strict=True)


@pytest.fixture
def catalogue(storage_path):
    return Catalogue(
        name="Test",
        path=storage_path,
        creation_date=datetime(2021, 1, 1, 22, 00, 30, tzinfo=timezone.utc),
        format_pattern="{filename}",
    )
