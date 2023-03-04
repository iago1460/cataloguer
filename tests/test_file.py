def test_file_split_extension(text_file):
    assert text_file.split_extension() == ("text-file", "txt")


def test_file_is_media_type(text_file):
    assert text_file.is_media_type() is False


def test_file_asdict(text_file):
    assert text_file.asdict() == {
        "hash": None,
        "path": str(text_file.path),
        "short_hash": None,
        "size": 0,
    }


def test_file_hash(catalogue, text_file):
    assert text_file.hash == "da39a3ee5e6b4b0d3255bfef95601890afd80709"
