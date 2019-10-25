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


def _normalize_datetime_format(exif_dt_field):
    exif_dt = exif_dt_field
    if type(exif_dt_field) in (tuple, list):
        if len(exif_dt_field) == 1:
            exif_dt = exif_dt_field[0]
    try:
        # format YYYY:MM:DD hh:mm:ss is not parsed correctly by dateutil
        return datetime.datetime.strptime(exif_dt, '%Y:%m:%d %H:%M:%S').isoformat()
    except ValueError:
        return exif_dt
    except TypeError:
        logging.info(f'Cannot parse "{exif_dt}", {exif_dt_field}')
        return None


def extract_created_date_from_exif(exif):
    created_data = exif.get('DateTimeOriginal') or exif.get('DateTime')

    created_data = _normalize_datetime_format(created_data)

    if created_data:
        return dateutil.parser.parse(created_data)
    return None


# def is_image(path):
#     try:
#         image = Image.open(path)
#     except IOError:
#         return False
#     else:
#         logging.debug(f'Format: {image.format}')
#         return True


def is_image(mime_type):
    return get_media_type(mime_type) == 'image'


def get_media_type(mime_type):
    return mime_type.split('/')[0]


def get_image_creation_date(path):
    try:
        image = Image.open(path)
    except IOError as e:
        logging.warning(e)
        return None
    try:
        metadata = get_exif(image)
    except AttributeError:
        logging.info(f'Cannot get metadata for {path}')
        return None
    return extract_created_date_from_exif(metadata)
