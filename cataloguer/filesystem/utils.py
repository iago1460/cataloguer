import hashlib
import os
from pathlib import Path


DATABASE_LOCATION = ".cataloguer_db.json"

KEEP_PARENT_FOLDERS = (  # TODO: undocumented behaviour
    "Time Lapse",
    "Burst Sequence",
)

UNITS = {1000: ["KB", "MB", "GB"], 1024: ["KiB", "MiB", "GiB"]}


def split_extension_from_filename(filename: str):
    name_split = filename.split(".")
    if len(name_split) > 1:
        return (".".join(name_split[0:-1]), name_split[-1])
    return (filename, "")


def _keep_parent_directory(path) -> str:
    parent_folder = path.parent.name
    if any(map(lambda pattern: parent_folder.startswith(pattern), KEEP_PARENT_FOLDERS)):
        return parent_folder
    return ""


def generate_filename(file, scr_data, unknown_format_pattern, path_format, import_dt):
    media_type, media_format = file.get_type()

    # FIXME: obscure logic to keep gopro directories
    # FIXME: bug if filename + relative_path is used
    parent_directory = _keep_parent_directory(file.path)
    relative_path = str(file.path.relative_to(scr_data.path).parent)

    uses_date = bool("%" in path_format)
    if not uses_date:
        return _generate_filename(
            file,
            path_format,
            dt=None,
            parent_directory=parent_directory,
            media_type=media_type,
            media_format=media_format,
            relative_path=relative_path,
        )

    created = file.get_creation_date()
    if created:
        return _generate_filename(
            file,
            path_format,
            dt=created,
            parent_directory=parent_directory,
            media_type=media_type,
            media_format=media_format,
            relative_path=relative_path,
        )

    if unknown_format_pattern:
        return _generate_filename(
            file,
            unknown_format_pattern,
            dt=import_dt,
            parent_directory=parent_directory,
            media_type=media_type,
            media_format=media_format,
            relative_path=relative_path,
        )

    return None


def _generate_filename(
    file, path_format, dt, parent_directory, media_type, media_format, relative_path
):
    file_name, file_extension = file.split_extension()
    name = Path(parent_directory or "").joinpath(file.path.name)
    strftime_format = path_format.format(
        file=name,
        file_extension=file_extension,
        file_name=file_name,
        media_type=media_type,
        media_format=media_format,
        relative_path=relative_path,
    )
    if dt:
        return dt.strftime(strftime_format)
    return strftime_format


def count_number_of_files(path):
    file_count = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for _ in filenames:
            file_count += 1
    return file_count


def _chunk_reader(fobj, chunk_size=1024):
    """Generator that reads a file in chunks of bytes"""
    while True:
        chunk = fobj.read(chunk_size)
        if not chunk:
            return
        yield chunk


def get_hash(path, first_chunk_only=False):
    hash_obj = hashlib.sha1()
    with open(path, "rb") as file_object:
        if first_chunk_only:
            hash_obj.update(file_object.read(1024))
        else:
            for chunk in _chunk_reader(file_object):
                hash_obj.update(chunk)
    return hash_obj.hexdigest()


def approximate_size(size, international_system=True):
    mult = 1000 if international_system else 1024
    for unit in UNITS[mult]:
        size = size / mult
        if size < mult:
            return "{0:.2f} {1}".format(size, unit)
