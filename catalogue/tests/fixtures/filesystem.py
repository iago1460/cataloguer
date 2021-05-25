from datetime import timezone, datetime

from pathlib import Path
from catalogue.model import File, Catalogue
import pytest


TEST_FILE_PATH = Path("tests/fixtures/test-files/text-file.txt").resolve()
TEST_CATALOGUE_PATH = Path("tests/fixtures/test-catalogue/").resolve()


@pytest.fixture
def text_file():
    assert TEST_FILE_PATH.exists()
    return File(TEST_FILE_PATH)


@pytest.fixture
def catalogue():
    assert TEST_CATALOGUE_PATH.exists()
    return Catalogue(
        TEST_CATALOGUE_PATH,
        last_update=datetime(2021, 1, 1, 22, 00, 30, tzinfo=timezone.utc),
    )
