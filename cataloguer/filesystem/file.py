import shutil
from contextlib import suppress
from pathlib import PurePath, Path

import magic

from .metadata import get_image_creation_date, get_path_creation_date
from .utils import get_hash, split_extension_from_filename


class Observable:
    def __init__(self):
        self._observers = set()

    def subscribe(self, observer):
        self._observers.add(observer)

    def unsubscribe(self, observer):
        with suppress(ValueError):
            self._observers.remove(observer)

    def notify(self, *args):
        for observer in list(self._observers):
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
        self.size = size or path.stat().st_size
        self._hash = hash
        self._short_hash = short_hash

    def __str__(self):
        return str(self.path or self._hash)

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
            self.hash = get_hash(self.path)
        return self._hash

    @hash.setter
    def hash(self, value):
        self.notify("hash", value)
        self._hash = value

    @property
    def short_hash(self):
        if self._short_hash is None:
            self.short_hash = get_hash(self.path, first_chunk_only=True)
        return self._short_hash

    @short_hash.setter
    def short_hash(self, value):
        self.notify("short_hash", value)
        self._short_hash = value

    def clone_file(self, new_path):
        # if new_path.exists():
        #     raise FileExistsError
        shutil.copy2(str(self.path), str(new_path))
        return File(
            path=new_path, size=self.size, hash=self._hash, short_hash=self._short_hash
        )

    def move_file(self, new_path):
        # if new_path.exists():
        #     raise FileExistsError
        shutil.move(self.path, new_path)
        self.path = new_path

    def delete(self):
        self.path.unlink()
        # TODO: delete parent folder if is empty too?
        self.path = None

    def split_extension(self):
        return split_extension_from_filename(self.path.name)

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
        media_type, _ = self.get_type()
        return media_type

    def get_type(self):
        mimetype = magic.from_file(str(self.path), mime=True)
        media_type = mimetype.split("/")[0]
        media_format = "/".join(mimetype.split("/")[1:])
        return media_type, media_format

    def asdict(self):
        return {
            "path": str(self._path),
            "size": self.size,
            "hash": self._hash,
            "short_hash": self._short_hash,
        }
