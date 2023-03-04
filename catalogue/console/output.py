from collections import Counter, defaultdict
from pathlib import Path

from rich import box
from rich.columns import Columns
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..console.default import console
from ..filesystem.utils import approximate_size


def print_processing(src_path: Path, dst_path: Path, imported_files, skipped_files):
    table = Table(
        show_header=True,
        show_footer=True,
        header_style="bold",
        box=box.SIMPLE,
        title=f"Processed files",
        # caption=f"Path: [b magenta]{catalogue.path}[/]"
    )
    table.border_style = "bright_yellow"
    table.add_column("Original Path", style="white")
    table.add_column("Destination Path", style="white")

    for original_path, file in imported_files:
        table.add_row(
            str(original_path.relative_to(src_path)),
            str(file.path.relative_to(dst_path)),
        )
    console.print(table)


def print_table_summary(duplicated_files, files, name):
    files_by_media = Counter((file.get_media_type() for file in files))
    files_size_by_media = defaultdict(int)
    for file in files:
        files_size_by_media[file.get_media_type()] += file.size
    duplicated_files_by_media = Counter(
        (file.get_media_type() for sublist in duplicated_files for file in sublist[:1])
    )
    table = Table(
        show_header=True,
        show_footer=True,
        header_style="bold",
        box=box.SIMPLE,
        # title=f'Catalogue: [b blue]{catalogue.name}',
        # caption=f"Path: [b magenta]{catalogue.path}[/]"
    )
    table.border_style = "bright_black"
    table.add_column(
        "Media Type", Text.from_markup("[b]Total", justify="right"), style="white"
    )
    table.add_column(
        "Size",
        approximate_size(sum(files_size_by_media.values())),
        justify="right",
        style="white",
        no_wrap=True,
    )
    table.add_column(
        "Files", str(len(files)), justify="right", style="white", no_wrap=True
    )
    table.add_column(
        "Duplicates",
        Text.from_markup(str(sum(duplicated_files_by_media.values())), style="red"),
        no_wrap=True,
        justify="right",
        style="red",
    )
    for file_type, count in files_by_media.items():
        prefix = "[dim]"
        if file_type in ("image", "video"):
            prefix = ""
        table.add_row(
            prefix + file_type,
            prefix + approximate_size(files_size_by_media[file_type]),
            prefix + str(count),
            prefix + str(duplicated_files_by_media.get(file_type, 0)),
        )
    # centered_table = Align.center(table)
    console.print(Markdown(f"# {name}"))
    console.print(table)


def print_duplicate_files(duplicated_files, from_path=None):
    console.print(Markdown("## Duplicates"))
    panels = []
    for duplicated_list in sorted(
        duplicated_files,
        key=lambda duplicated_list: duplicated_list[0].size,
        reverse=True,
    ):
        if from_path:
            filenames = [
                str(file.path.relative_to(from_path)) for file in duplicated_list
            ]
        else:
            filenames = [file.path.name for file in duplicated_list]

        items = []
        for path, count in Counter(filenames).items():
            text = path
            if count > 1:
                text = f"{path} (x{count})"
            items.append(text)
        panels.append(
            Panel(
                "\n".join(items),
                border_style="bright_black",
                expand=True,
                title=approximate_size(duplicated_list[0].size),
            )
        )
    console.print(Columns(panels))
