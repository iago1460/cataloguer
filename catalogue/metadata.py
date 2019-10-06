import datetime
import logging

import PIL.ExifTags
import dateutil.parser
from PIL import Image
from PIL.TiffTags import TAGS


def get_exif(image):
    if image.format == 'TIFF':
        return {TAGS[key]: image.tag[key] for key in image.tag.keys()}
    return {
        PIL.ExifTags.TAGS[k]: v
        for k, v in image._getexif().items()
        if k in PIL.ExifTags.TAGS
    }


def _normalize_datetime_format(exif_dt):
    if type(exif_dt) in (tuple, list):
        if len(exif_dt) == 1:
            exif_dt = exif_dt[0]
    try:
        # format YYYY:MM:DD hh:mm:ss is not parsed correctly by dateutil
        return datetime.datetime.strptime(exif_dt, '%Y:%m:%d %H:%M:%S').isoformat()
    except ValueError:
        return exif_dt


def extract_created_date_from_exif(exif):
    created_data = exif.get('DateTimeOriginal') or exif.get('DateTime')

    created_data = _normalize_datetime_format(created_data)

    if created_data:
        return dateutil.parser.parse(created_data)
    return None


def is_image(path):
    if path.is_file():
        try:
            image = Image.open(path)
        except IOError:
            return False
        else:
            logging.debug(f'Format: {image.format}')
            return True
    return False


def get_image_creation_date(path):
    image = Image.open(path)
    metadata = get_exif(image)
    return extract_created_date_from_exif(metadata)
