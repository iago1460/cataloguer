import json
import hashlib
import logging
import magic
import os
import shutil
from itertools import chain
from pathlib import PurePath, Path
from contextlib import suppress
from catalogue.metadata import get_image_creation_date, get_path_creation_date

from datetime import datetime, timezone, timedelta
from catalogue import __version__


CATALOGUE_EXPIRY_DELTA = timedelta(days=1)


class Observable:
    def __init__(self):
        self._observers = set()

    def subscribe(self, observer):
        self._observers.add(observer)

    def unsubscribe(self, observer):
        with suppress(ValueError):
            self._observers.remove(observer)

    def notify(self, *args):
        for observer in self._observers:
            observer.notify(self, *args)


class File(Observable):
    _path: Path
    size: int
    _hash: int
    _short_hash: int

    def __init__(self, path, size=None, hash=None, short_hash=None):
        super().__init__()
        if not isinstance(path, PurePath):
            path = Path(path)
        self._path = path
        self.size = size
        self._hash = hash
        self._short_hash = short_hash

    def __str__(self):
        if self.path:
            return str(self.path)

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self.notify("path", value)
        self._path = value

    @property
    def hash(self):
        if self._hash is None:
            self.hash = _get_hash(self.path)
        return self._hash

    @hash.setter
    def hash(self, value):
        self.notify("hash", value)
        self._hash = value

    @property
    def short_hash(self):
        if self._short_hash is None:
            self.short_hash = _get_hash(self.path, first_chunk_only=True)
        return self._short_hash

    @short_hash.setter
    def short_hash(self, value):
        self.notify("short_hash", value)
        self._short_hash = value

    def clone_file(self, new_path):
        # if new_path.exists():
        #     raise FileExistsError
        create_dst_folder(new_path.parent)
        shutil.copy2(str(self.path), str(new_path))
        return File(
            path=new_path, size=self.size, hash=self._hash, short_hash=self._short_hash
        )

    def move_file(self, new_path):
        # if new_path.exists():
        #     raise FileExistsError
        create_dst_folder(new_path.parent)
        shutil.move(self.path, new_path)
        self.path = new_path

    def split_extension(self):
        filename = self.path.name
        return split_extension(filename)

    def get_creation_date(self):
        creation_date = None
        if self.is_image():
            creation_date = get_image_creation_date(self.path)
        if not creation_date:
            creation_date = get_path_creation_date(self.path)
        return creation_date

    def is_media_type(self):
        return self.is_image() or self.is_video()

    def is_image(self):
        return self.get_media_type() == "image"

    def is_video(self):
        return self.get_media_type() == "video"

    def get_media_type(self):
        mime_type = magic.from_file(str(self.path), mime=True)
        simple_mime_type = mime_type.split("/")[0]
        return simple_mime_type

    def asdict(self):
        return {
            "path": str(self._path),
            "size": self.size,
            "hash": self._hash,
            "short_hash": self._short_hash,
        }


DATABASE_LOCATION = ".catalogue_db.json"


class Catalogue:
    root_path = None
    last_update = None
    files = None
    _files_by_path = None
    _files_by_size = None
    _files_by_short_hash = None
    _files_by_hash = None

    def __init__(self, root_path: Path, files=None, last_update=None):
        self.root_path = root_path
        self.files = []
        self.last_update = last_update
        self._files_by_path = {}
        self._files_by_size = {}
        self._files_by_short_hash = {}
        self._files_by_hash = {}
        if files:
            list(map(self.add_file, files))

    @classmethod
    def load(cls, path):
        db_data = cls._load_data_from_database(path)
        if db_data:
            last_update = datetime.fromisoformat(db_data["last_update"])
            if (
                db_data["version"] == __version__
                or datetime.now(timezone.utc) - last_update < CATALOGUE_EXPIRY_DELTA
            ):
                logging.debug(
                    "Database file seems suitable, using it to speed up things!"
                )
                files = [
                    File(**{**file_data, "path": path.joinpath(file_data["path"])})
                    for file_data in db_data["files"]
                ]
                return cls(path, files=files, last_update=last_update)
            logging.debug("Database seems outdated, reverting to scan...")

        return cls._generate_catalogue_from_scan(path)

    @classmethod
    def _load_data_from_database(cls, path):
        db_path = path.joinpath(DATABASE_LOCATION)
        if db_path.exists():
            with open(db_path) as json_file:
                try:
                    return json.load(json_file)
                except json.JSONDecodeError:
                    logging.warning("DB file is corrupted, ignoring...")
        return None

    @classmethod
    def _generate_catalogue_from_scan(cls, path):
        files = []
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                try:
                    # if the target is a symlink (soft one), this will
                    # dereference it - change the value to the actual target file
                    file_path = Path(os.path.realpath(full_path))
                    file_size = os.path.getsize(file_path)
                except OSError as e:
                    # not accessible (permissions, etc) - pass on
                    logging.warning("Cannot read %s: %s", full_path, e)
                    continue
                files.append(File(path=file_path, size=file_size))
        return cls(root_path=path, files=files, last_update=datetime.now(timezone.utc))

    def notify(self, file, field, new_value):
        """
        Observer notification method
        """
        if field == "path":
            del self._files_by_path[file.path]
            if not new_value.is_relative_to(self.root_path):
                file.unsubscribe(self)
                with suppress(ValueError):
                    self.files.remove(file)
                with suppress(ValueError):
                    self._files_by_size.setdefault(file.size, []).remove(file)
                with suppress(ValueError):
                    self._files_by_short_hash.setdefault(file._short_hash, []).remove(file)
                with suppress(ValueError):
                    self._files_by_hash.setdefault(file._hash, []).remove(file)
                return
            self._files_by_path[new_value] = file
        elif field == "short_hash":
            self._files_by_short_hash.setdefault(new_value, []).append(file)
        elif field == "hash":
            self._files_by_hash.setdefault(new_value, []).append(file)

    def add_file(self, file):
        file.subscribe(self)
        self.files.append(file)
        self._files_by_path[file.path] = file
        self._files_by_size.setdefault(file.size, []).append(file)
        if file._short_hash:
            self._files_by_short_hash.setdefault(file._short_hash, []).append(file)
        if file._hash:
            self._files_by_hash.setdefault(file._hash, []).append(file)

    @staticmethod
    def detect_duplicates_on_files(files_by_size):
        _files_by_hash = {}
        _files_by_short_hash = {}
        file_size_collisions = filter(
            lambda items: len(items) > 1, files_by_size.values()
        )
        for file in chain(*file_size_collisions):
            short_file_hash = file.short_hash
            _files_by_short_hash.setdefault(short_file_hash, []).append(file)

        short_file_hash_collisions = filter(
            lambda items: len(items) > 1, _files_by_short_hash.values()
        )
        for file in chain(*short_file_hash_collisions):
            file_hash = file.hash
            _files_by_hash.setdefault(file_hash, []).append(file)

        file_hash_collisions = filter(
            lambda items: len(items) > 1, _files_by_hash.values()
        )
        return list(file_hash_collisions)

    def detect_duplicates(self):
        return self.detect_duplicates_on_files(files_by_size=self._files_by_size)

    def detect_duplicates_with(self, catalogue):
        def intersect(a, b):
            return {k: list(chain(a[k], b[k])) for k in a.keys() & b.keys()}

        files_by_size = intersect(self._files_by_size, catalogue._files_by_size)
        return self.detect_duplicates_on_files(files_by_size=files_by_size)

    def is_path_available(self, path):
        return self._files_by_path.get(path) is None

    def find_new_path(self, path):
        basename, filename_extension = split_extension(path.name)
        i = 0
        while True:
            i += 1
            new_filename = f"{basename}_{i}.{filename_extension}"
            new_path = Path(path.parent.joinpath(new_filename))
            if self._files_by_path.get(new_path) is None:
                return new_path

    def asdict(self):
        def file_asdict(file):
            file_dict = file.asdict()
            file_dict["path"] = str(file.path.relative_to(self.root_path))
            return file_dict

        return {
            "version": __version__,
            "last_update": self.last_update.isoformat(),
            "files": [file_asdict(file) for file in self.files],
        }

    def save_db(self):
        db_path = self.root_path.joinpath(DATABASE_LOCATION)
        db_data = self.asdict()
        with open(db_path, "w") as db_file:
            # json.dump(db_data, db_file, indent=4) # debug
            json.dump(db_data, db_file)


def create_dst_folder(path_folder):
    if not path_folder.exists():
        logging.debug(f'Creating folder "{path_folder}"')
        os.makedirs(path_folder)


def split_extension(name):
    name_split = name.split(".")
    if len(name_split) > 1:
        return ".".join(name_split[0:-1]), name_split[-1]
    return name, ""


def _chunk_reader(fobj, chunk_size=1024):
    """Generator that reads a file in chunks of bytes"""
    while True:
        chunk = fobj.read(chunk_size)
        if not chunk:
            return
        yield chunk


def _get_hash(path, first_chunk_only=False):
    hash_obj = hashlib.sha1()
    with open(path, "rb") as file_object:
        if first_chunk_only:
            hash_obj.update(file_object.read(1024))
        else:
            for chunk in _chunk_reader(file_object):
                hash_obj.update(chunk)
    return hash_obj.hexdigest()
