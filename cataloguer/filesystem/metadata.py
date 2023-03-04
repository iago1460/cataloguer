import datetime
import logging
import re

import PIL.ExifTags
import dateutil.parser
from PIL import Image
from PIL.TiffTags import TAGS


DATE_PATH_REGEXES = (
    r"/(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})",
    r"/IMG_(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})_",
    r"/VID_(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})_",
    r"/IMG-(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})-",
)


def get_path_creation_date(path):
    for regex in DATE_PATH_REGEXES:
        match = re.search(regex, str(path))
        if match:
            year, month, day = match.groups()
            try:
                return datetime.datetime(year=int(year), month=int(month), day=int(day))
            except ValueError:
                pass
    return None


def get_image_creation_date(path):
    try:
        image = Image.open(path)
    except IOError as e:
        logging.warning(e)  # cannot identify image file
        return None

    try:
        metadata = _get_exif(image)
    except AttributeError as e:
        logging.debug(f"Cannot get exif metadata for {path}")
        return None

    try:
        return _extract_created_date_from_exif(metadata)
    except ValueError:
        logging.debug(f"Cannot get creation date from exif metadata for {path}")
        return None


def _get_exif(image):
    if image.format == "TIFF":
        return {TAGS.get(key): image.tag[key] for key in image.tag.keys()}
    return {
        PIL.ExifTags.TAGS[k]: v
        for k, v in image._getexif().items()
        if k in PIL.ExifTags.TAGS
    }


def _normalize_datetime_format(exif_dt_field):
    exif_dt = exif_dt_field
    if type(exif_dt_field) in (tuple, list):
        if len(exif_dt_field) == 1:
            exif_dt = exif_dt_field[0]
    try:
        # format YYYY:MM:DD hh:mm:ss is not parsed correctly by dateutil
        return datetime.datetime.strptime(exif_dt, "%Y:%m:%d %H:%M:%S").isoformat()
    except ValueError:
        return exif_dt
    except TypeError:
        logging.debug(f"Cannot parse {exif_dt=}")
        return None


def _extract_created_date_from_exif(exif):
    exif_dt_field = exif.get("DateTimeOriginal") or exif.get("DateTime")

    if not exif_dt_field:
        return None

    created_data = _normalize_datetime_format(exif_dt_field)
    if not created_data:
        return None

    try:
        return dateutil.parser.parse(created_data)
    except ValueError as e:
        if e.args[0] == "Unknown string format: %s":
            unknown_date = e.args[1]
            logging.debug(f"Attempting to parse unknown date {unknown_date}")
            match = re.search(
                r"(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})", unknown_date
            )
            if match:
                year, month, day = match.groups()
                return datetime.datetime(year=int(year), month=int(month), day=int(day))
        raise e
