import pytest
from pydantic import BaseModel

from cataloguer.filesystem.utils import split_extension_from_filename


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
    assert expected == split_extension_from_filename(raw_value)


def test_pydantic_hash_override():
    class TestHash(BaseModel):
        id: int
        data: str

        def __hash__(self):
            return self.id

        def __eq__(self, other):
            return self.id == other.id

    obj_id_1 = TestHash(id=1, data="first")
    obj_id_2 = TestHash(id=2, data="second")
    obj_id_1_with_new_data = TestHash(id=2, data="third")

    assert {obj_id_1, obj_id_2, obj_id_1_with_new_data} == {obj_id_1, obj_id_2}
