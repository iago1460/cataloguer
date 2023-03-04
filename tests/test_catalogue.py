from catalogue.filesystem.directory import Catalogue


def test_catalogue_serialization(catalogue, text_file):
    test_file_path = catalogue.path.joinpath("text.txt")
    test_file = text_file.clone_file(test_file_path)
    catalogue.add_file(test_file)

    assert catalogue.dict() == Catalogue.parse_obj(catalogue.dict()).dict()


def test_catalogue_smart_loader(catalogue, text_file):
    test_file_path = catalogue.path.joinpath("text.txt")
    test_file = text_file.clone_file(test_file_path)
    catalogue.add_file(test_file)

    # Faking catalogue file which has disappeared by a thrid party
    test_file_path.unlink()

    assert not Catalogue.parse_obj(catalogue.dict()).dict()["files"]


def test_catalogue_subscribes_for_file_changes(catalogue, text_file):
    test_file_path = catalogue.path.joinpath("text.txt")
    test_file = text_file.clone_file(test_file_path)
    catalogue.add_file(test_file)

    test_file.hash = "new"

    assert catalogue.dict()["files"][0]["hash"] == "new"
