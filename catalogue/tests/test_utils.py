import pytest

from catalogue.model import split_extension


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    (
        ("filename.txt", ("filename", "txt")),
        ("filename", ("filename", "")),
        (".txt", ("", "txt")),
        ("filename.old.txt", ("filename.old", "txt")),
    ),
)
def test_split_extension(raw_value, expected):
    assert expected == split_extension(raw_value)


def test_file_split_extension(text_file):
    assert text_file.split_extension() == ("text-file", "txt")


def test_file_is_media_type(text_file):
    assert text_file.is_media_type() is False


def test_file_asdict(text_file):
    assert text_file.asdict() == {
        "hash": None,
        "path": str(text_file.path),
        "short_hash": None,
        "size": None,
    }


def test_catalogue_asdict(catalogue, text_file):
    text_file.path = catalogue.root_path.joinpath("folder/text.txt")
    catalogue.add_file(text_file)
    assert catalogue.asdict() == {
        "files": [
            {"hash": None, "path": "folder/text.txt", "short_hash": None, "size": None}
        ],
        "last_update": "2021-01-01T22:00:30+00:00",
        "version": "1.0",
    }


def test_add_file_to_catalogue(catalogue, text_file):
    assert len(catalogue.files) == 0
    catalogue.add_file(text_file)
    assert len(catalogue.files) == 1


def test_add_file_to_catalogue_subscribes_for_changes(catalogue, text_file):
    catalogue.add_file(text_file)
    assert catalogue._files_by_hash == {}

    text_file.hash = 999
    assert catalogue._files_by_hash == {999: [text_file]}
