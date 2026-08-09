import datetime
from pathlib import Path

import pytest
from PIL import ExifTags, Image
from PIL.TiffImagePlugin import ImageFileDirectory_v2

from cataloguer.filesystem.metadata import (
    get_image_creation_date,
    get_path_creation_date,
)

TEST_FILES = Path(__file__).parent / "fixtures" / "test-files"


def _write_jpeg(path, date_time=None, date_time_original=None):
    """
    Write a JPEG placing DateTime in the base IFD and DateTimeOriginal in the
    Exif sub-IFD, which is where cameras actually put them.
    """
    image = Image.new("RGB", (16, 16), (255, 0, 0))
    exif = image.getexif()
    if date_time:
        exif[ExifTags.Base.DateTime] = date_time
    if date_time_original:
        exif.get_ifd(ExifTags.IFD.Exif)[
            ExifTags.Base.DateTimeOriginal
        ] = date_time_original
    image.save(path, exif=exif)
    return path


def test_datetime_original_lives_only_in_the_exif_sub_ifd(tmp_path):
    """
    Regression guard for the Pillow upgrade trap.

    Pillow's public Image.getexif() returns the base IFD only, and
    DateTimeOriginal is not in it. Any implementation that reads just
    getexif().items() loses the capture date silently - no exception, no
    warning, files simply stop being dated correctly. This test pins the
    underlying Pillow behaviour so the cause stays obvious.
    """
    path = _write_jpeg(tmp_path / "sub_ifd.jpg", date_time_original="2019:08:22 21:31:25")

    with Image.open(path) as image:
        base_ifd = {ExifTags.TAGS.get(k) for k in image.getexif().keys()}
        sub_ifd = {
            ExifTags.TAGS.get(k)
            for k in image.getexif().get_ifd(ExifTags.IFD.Exif).keys()
        }

    assert "DateTimeOriginal" not in base_ifd
    assert "DateTimeOriginal" in sub_ifd


def test_creation_date_from_exif_sub_ifd(tmp_path):
    path = _write_jpeg(tmp_path / "sub_ifd.jpg", date_time_original="2019:08:22 21:31:25")

    assert get_image_creation_date(path) == datetime.datetime(2019, 8, 22, 21, 31, 25)


def test_date_time_original_wins_over_date_time(tmp_path):
    path = _write_jpeg(
        tmp_path / "both.jpg",
        date_time="2020:01:02 03:04:05",
        date_time_original="2019:08:22 21:31:25",
    )

    assert get_image_creation_date(path) == datetime.datetime(2019, 8, 22, 21, 31, 25)


def test_creation_date_falls_back_to_base_ifd_date_time(tmp_path):
    path = _write_jpeg(tmp_path / "base_only.jpg", date_time="2020:01:02 03:04:05")

    assert get_image_creation_date(path) == datetime.datetime(2020, 1, 2, 3, 4, 5)


def test_creation_date_from_tiff_tags(tmp_path):
    path = tmp_path / "tagged.tiff"
    ifd = ImageFileDirectory_v2()
    ifd[ExifTags.Base.DateTime] = "2018:03:04 05:06:07"
    Image.new("RGB", (16, 16), (0, 255, 0)).save(path, tiffinfo=ifd)

    assert get_image_creation_date(path) == datetime.datetime(2018, 3, 4, 5, 6, 7)


def test_image_without_exif_returns_none(tmp_path):
    path = tmp_path / "no_exif.jpg"
    Image.new("RGB", (8, 8)).save(path)

    assert get_image_creation_date(path) is None


def test_non_image_file_returns_none():
    assert get_image_creation_date(TEST_FILES / "text-file.txt") is None


@pytest.mark.parametrize(
    ("filename", "expected"),
    (
        ("/photos/2019-08-22 holidays/x.jpg", datetime.datetime(2019, 8, 22)),
        ("/photos/IMG_20190822_213125.jpg", datetime.datetime(2019, 8, 22)),
        ("/photos/VID_20190822_213125.mp4", datetime.datetime(2019, 8, 22)),
        ("/photos/IMG-20190822-WA0001.jpg", datetime.datetime(2019, 8, 22)),
        ("/photos/no-date-here.jpg", None),
        ("/photos/2019-13-45 impossible/x.jpg", None),
    ),
)
def test_get_path_creation_date(filename, expected):
    assert get_path_creation_date(Path(filename)) == expected
