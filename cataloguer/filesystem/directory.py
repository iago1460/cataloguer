import json
import logging
import os
from contextlib import suppress

from datetime import datetime, timezone
from itertools import chain
from pathlib import Path
from typing import List, Dict, Optional
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    MofNCompleteColumn,
    TimeRemainingColumn,
    SpinnerColumn,
    TimeElapsedColumn,
)

from .file import File
from .utils import split_extension_from_filename, count_number_of_files
from ..console.default import console

DATABASE_LOCATION = ".cataloguer_db.json"

logger = logging.getLogger(__name__)


class Directory:
    path = None
    _files: List[File] = None
    _files_by_path: Dict[Path, File] = None
    _files_by_size: Dict[int, File] = None

    @property
    def files(self):
        return tuple(self._files.copy())

    @files.setter
    def files(self, value):
        list(map(self.add_file, value))
        self._files = value

    def __init__(self, path: Path, files: Optional[List[File]] = None):
        self.path = path.resolve()
        self._files_by_path = {}
        self._files_by_size = {}
        self.files = files or []

    @classmethod
    def from_path(cls, path: Path):
        directory = cls(path=path)
        directory.explore()
        return directory

    def explore(self):
        files = []

        # with Progress(
        #     TextColumn(f"[green]Exploring {self.path.name}..."),
        #     BarColumn(),
        #     TextColumn("[progress.description]{task.description}"),
        # ) as progress:
        #     discovery_task = progress.add_task("Exploring repo", total=None)

        with console.status(
            f"[green]Exploring {self.path.name}...",
        ) as status:
            for dirpath, dirnames, filenames in os.walk(self.path):
                for filename in filenames:
                    full_path = os.path.join(dirpath, filename)
                    try:
                        # if the target is a symlink (soft one), this will
                        # dereference it - change the value to the actual target file
                        file_path = Path(os.path.realpath(full_path))
                        file_size = os.path.getsize(file_path)
                    except OSError as e:
                        # not accessible (permissions, etc) - pass on
                        logger.warning("Cannot read %s: %s", full_path, e)
                        continue
                    files.append(File(path=file_path, size=file_size))
                    # progress.update(discovery_task, description=f"Found {len(files)} files")
                status.update(
                    status=f"[green]Exploring {self.path.name}. Found {len(files)} files"
                )
            # progress.update(discovery_task, total=len(files), completed=len(files))

        self.files = files
        return files

    def notify(self, file, field, new_value):
        """
        Observer notification method
        """
        if field == "path":
            del self._files_by_path[file.path]
            # if not new_value.is_relative_to(self.path): # New in version 3.9
            if not str(new_value or "").startswith(str(self.path)):
                file.unsubscribe(self)
                with suppress(ValueError):
                    self._files.remove(file)
                with suppress(ValueError):
                    self._files_by_size.setdefault(file.size, []).remove(file)
                    if not self._files_by_size[file.size]:
                        del self._files_by_size[file.size]
                return
            self._files_by_path[new_value] = file

    def add_file(self, file):
        file.subscribe(self)
        self._files.append(file)
        self._files_by_path[file.path] = file
        self._files_by_size.setdefault(file.size, []).append(file)

    @staticmethod
    def detect_duplicates_on_files(files_by_size) -> List[List[File]]:
        _files_by_hash = {}
        _files_by_short_hash = {}
        file_size_collisions = filter(
            lambda items: len(items) > 1, files_by_size.values()
        )
        file_size_collisions = list(chain(*file_size_collisions))

        # with Progress(
        #     TextColumn("[progress.description]{task.description}"),
        #     BarColumn(),
        #     TaskProgressColumn(),
        #     MofNCompleteColumn(),
        #     TimeRemainingColumn(),
        #     # expand=True,
        #     # transient=True
        # ) as progress:
        #     file_size_collisions = list(chain(*file_size_collisions))
        #     fast_detection_task = progress.add_task("[green]Quick file inspection", total=len(file_size_collisions))
        #     slow_detection_task = progress.add_task("[green]Inspecting full files", total=None)
        with console.status(f"[green]Inspecting files for duplication...") as status:
            for index, file in enumerate(file_size_collisions, start=1):
                # progress.update(fast_detection_task, completed=index)
                short_file_hash = file.short_hash
                _files_by_short_hash.setdefault(short_file_hash, []).append(file)

            short_file_hash_collisions = filter(
                lambda items: len(items) > 1, _files_by_short_hash.values()
            )

            short_file_hash_collisions = list(chain(*short_file_hash_collisions))
            # progress.update(slow_detection_task, total=len(short_file_hash_collisions))
            for index, file in enumerate(short_file_hash_collisions, start=1):
                # progress.update(slow_detection_task, completed=index)
                status.update(
                    status=f"[green]Inspecting file {index} of {len(short_file_hash_collisions)} for duplicates"
                )
                file_hash = file.hash
                _files_by_hash.setdefault(file_hash, []).append(file)

            file_hash_collisions = filter(
                lambda items: len(items) > 1, _files_by_hash.values()
            )
            return list(file_hash_collisions)

    def detect_duplicates(self, media_only=True):
        files_by_size = self._files_by_size
        if media_only:
            files_by_size = {
                size: files
                for size, files in self._files_by_size.items()
                if files[0].is_media_type()
            }
        return self.detect_duplicates_on_files(files_by_size=files_by_size)

    def detect_duplicates_with(self, files, media_only=True):
        def intersect(a, b):
            return {k: list(chain(a[k], b[k])) for k in a.keys() & b.keys()}

        files_by_size = self._files_by_size
        if media_only:
            files_by_size = {
                size: files
                for size, files in self._files_by_size.items()
                if files[
                    0
                ].is_media_type()  # if one of them is media type, all are since are duplicates
            }

        given_files_by_size = {}
        for file in files:
            given_files_by_size.setdefault(file.size, []).append(file)

        intersection_of_files_by_size = intersect(files_by_size, given_files_by_size)
        return self.detect_duplicates_on_files(
            files_by_size=intersection_of_files_by_size
        )

    def is_path_available(self, path):
        return self._files_by_path.get(path) is None

    def find_new_path(self, path):
        basename, filename_extension = split_extension_from_filename(path.name)
        i = 0
        while True:
            i += 1
            new_filename = f"{basename}_{i}.{filename_extension}"
            new_path = Path(path.parent.joinpath(new_filename))
            if self._files_by_path.get(new_path) is None:
                return new_path


class Catalogue(Directory):
    name: str
    creation_date: datetime
    format_pattern: str
    unknown_format_pattern: Optional[str]

    def __init__(
        self,
        name: str,
        format_pattern: str,
        unknown_format_pattern: Optional[str] = None,
        creation_date: datetime = None,
        **kwargs,
    ):
        self.name = name
        self.format_pattern = format_pattern
        self.unknown_format_pattern = unknown_format_pattern
        self.creation_date = creation_date or datetime.now(timezone.utc)
        super().__init__(**kwargs)

    def dict(self):
        def file_asdict(file):
            file_dict = file.asdict()
            file_dict["path"] = str(file.path.relative_to(self.path))
            return file_dict

        return {
            "name": self.name,
            "path": self.path.resolve(),
            "creation_date": self.creation_date.isoformat(),
            "format_pattern": self.format_pattern,
            "unknown_format_pattern": self.unknown_format_pattern,
            "files": [file_asdict(file) for file in self._files],
        }

    def save(self, path: Path):
        catalogue_data = self.dict()
        with open(path, "w") as fd:
            json.dump(catalogue_data, fd, default=str)

    @classmethod
    def parse_obj(cls, data, force_reload=False):
        path = Path(data["path"]).resolve(strict=True)
        creation_date = datetime.fromisoformat(data["creation_date"])
        catalogue = cls(
            name=data["name"],
            path=path,
            creation_date=creation_date,
            format_pattern=data["format_pattern"],
            unknown_format_pattern=data.get("unknown_format_pattern"),
        )
        files_on_path = count_number_of_files(path)
        logger.debug(
            f"Catalogue files: {len(data['files'])} vs filesystem files {files_on_path}"
        )
        if force_reload or len(data["files"]) != files_on_path:
            catalogue.explore()
        else:
            files = [
                File(**{**file_data, "path": path.joinpath(file_data["path"])})
                for file_data in data["files"]
            ]
            catalogue.files = files
        return catalogue
