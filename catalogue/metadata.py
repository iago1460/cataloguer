import datetime
import logging
import re

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
        try:
            return dateutil.parser.parse(created_data)
        except ValueError as e:
            if e.args[0] == 'Unknown string format: %s':
                unknown_date = e.args[1]
                logging.info(f'Attempting to parse unknown date {unknown_date}')
                match = re.search(r'(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})', unknown_date)
                if match:
                    year, month, day = match.groups()
                    return datetime.datetime(year=int(year), month=int(month), day=int(day))
            logging.error(e)
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


def is_video(mime_type):
    return get_media_type(mime_type) == 'video'


def get_media_type(mime_type):
    return mime_type.split('/')[0]


def get_creation_date(path, mime_type):
    creation_date = None
    if is_image(mime_type):
        creation_date = get_image_creation_date(path)
    if not creation_date:
        creation_date = get_path_creation_date(path)
    return creation_date


def get_path_creation_date(path):
    match = re.search(r"/(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})", str(path))
    if match:
        year, month, day = match.groups()
        try:
            return datetime.datetime(year=int(year), month=int(month), day=int(day))
        except ValueError:
            return None
    return None


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
