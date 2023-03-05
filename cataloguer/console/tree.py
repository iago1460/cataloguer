from pathlib import Path
from typing import List, Set

from pydantic import BaseModel
from rich.markup import escape
from rich.tree import Tree

from ..filesystem.file import File
from ..filesystem.utils import approximate_size


class FileInfo(BaseModel):
    file: File
    old_path: Path

    @property
    def path(self):
        return self.file.path or self.old_path

    def __hash__(self):
        return self.path.__hash__()

    def __eq__(self, other):
        return self.path == other.path

    class Config:
        arbitrary_types_allowed = True


class DirectoryInfo(BaseModel):
    path: Path
    files: Set[FileInfo]
    sub_directories: Set["DirectoryInfo"]

    def __hash__(self):
        return self.path.__hash__()

    def __eq__(self, other):
        return self.path == other.path


class DirectoryTree:
    tree: dict
    file_count: int = 0

    def __init__(self):
        self.tree = {}

    def add_imported_file(self, file, old_path):
        parent_directory_info = None

        if file.path is None:
            path = old_path  # file was deleted
        else:
            path = file.path

        for directory_path in _get_parents(path.parent):
            directory_info = self.tree.setdefault(
                directory_path,
                DirectoryInfo(path=directory_path, files=[], sub_directories=[]),
            )
            if parent_directory_info:
                parent_directory_info.sub_directories.add(directory_info)
            parent_directory_info = directory_info

        self.file_count += 1
        directory_info.files.add(
            FileInfo(
                file=file,
                old_path=old_path,
            )
        )

    def generate_tree(self, dst_path, guide_style="bold bright_blue"):
        directory_info = self.tree.get(dst_path)
        if not directory_info:
            return None
        tree = Tree(
            f":open_file_folder: [link file://{directory_info.path}]{escape(directory_info.path.name)}",
            guide_style=guide_style,
        )
        _expand_tree(tree=tree, directory_info=directory_info)
        return tree


def _expand_tree(tree, directory_info: DirectoryInfo):
    for file_info in directory_info.files:
        if file_info.file.path is None:
            tree.add(
                f"{file_info.old_path.name} [b green]{approximate_size(file_info.file.size)}"
            )
        elif file_info.old_path.name != file_info.file.path.name:
            tree.add(
                f"{file_info.file.path.name} ({file_info.old_path.name}) [b bright_yellow]{approximate_size(file_info.file.size)}"
            )
        else:
            tree.add(
                f"{file_info.file.path.name} [b bright_yellow]{approximate_size(file_info.file.size)}"
            )

    for sub_directory_info in sorted(
        directory_info.sub_directories, key=lambda directory: directory.path
    ):
        branch = tree.add(
            f":open_file_folder: [b bold][link file://{sub_directory_info.path}]{escape(sub_directory_info.path.name)}[/]"
        )
        _expand_tree(tree=branch, directory_info=sub_directory_info)


def _get_parents(path: Path) -> List[Path]:
    directories = []
    while path != Path("/"):
        directories.append(path)
        path = path.parent
    directories.reverse()
    return directories
