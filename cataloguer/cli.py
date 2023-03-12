import logging
from contextlib import suppress
from datetime import timezone, datetime
from enum import Enum
from itertools import chain
from pathlib import Path

import rich_click as click
from pydantic import BaseModel
from rich.prompt import Confirm

from .console.default import console
from .console.output import print_table_summary, print_duplicate_files
from .console.tree import DirectoryTree
from .filesystem.directory import Catalogue, Directory
from .filesystem.file import File
from .filesystem.utils import generate_filename
from .settings import GlobalSettings
from .storage import Storage

click.rich_click.SHOW_ARGUMENTS = True
# click.rich_click.GROUP_ARGUMENTS_OPTIONS = True


class Context(BaseModel):
    global_settings: GlobalSettings
    storage: Storage
    workdir: Path
    verbose: bool
    interactive: bool


class Operation(Enum):
    MOVE = "move"
    COPY = "copy"
    DELETE = "delete"

    def __str__(self):
        return self.value


@click.group(context_settings={"auto_envvar_prefix": "CATALOGUER"})
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enables verbose mode. Disabled by default",
    default=False,
)
@click.option("--format-pattern", help='Pattern template. e.g. %Y/%m/{file}', required=False)
@click.option("--unknown-format-pattern", help='Pattern template fallback when date cannot get extracted', required=False)
@click.option(
    "--interactive/--no-interactive",
    help="Disables confirmation prompts. Enabled by default",
    default=True,
)
@click.pass_context
def cli(ctx, verbose, interactive, format_pattern, unknown_format_pattern):
    """
    Command line interface.

    All [OPTIONS] can be passed as environment variables with the "CATALOGUER_" prefix.

    file arguments accept file names and a special value "-" to indicate stdin or stdout
    """
    if not ctx.obj:
        global_settings = GlobalSettings(format_pattern=format_pattern, unknown_format_pattern=unknown_format_pattern)
        ctx.obj = Context(
            global_settings=global_settings,
            storage=Storage(path=global_settings.storage_location),
            workdir=Path.cwd(),
            verbose=verbose,
            interactive=interactive,
        )
        if verbose:
            console.print(ctx.obj)


@cli.command()
@click.argument("src")
@click.option(
    "--media-only/--all", help="Filter by media files. Enabled by default", default=True
)
@click.pass_obj
def inspect(ctx: Context, src, media_only):
    """
    Inspects a path or a catalogue
    """
    # TODO: allow single file
    directory = ctx.storage.load_catalogue(src, force_reload=True)
    if not directory:
        src_path = None
        with suppress(FileNotFoundError):
            src_path = Path(src).expanduser().resolve(strict=True)
        if not src_path or not src_path.is_dir():
            raise click.BadParameter(
                f'Error "{src}" is neither a catalogue or an existing directory'
            )
        directory = Directory.from_path(src_path)

    duplicated_files = directory.detect_duplicates(media_only=media_only)
    with console.status(
        "[green]Preparing summary...",
    ):
        name = directory.path
        if isinstance(directory, Catalogue):
            name = f"{directory.name} : {directory.path}"

        files = directory.files
        if media_only:
            files = [file for file in files if file.is_media_type()]
        print_table_summary(name=name, files=files, duplicated_files=duplicated_files)

        if duplicated_files:
            duplicated_list_of_files_sorted_by_name_length = list(
                sorted(duplicated_list, key=lambda file: (len(file.path.name), len(str(file.path))))
                for duplicated_list in duplicated_files
            )
            print_duplicate_files(
                duplicated_files=duplicated_list_of_files_sorted_by_name_length, from_path=directory.path
            )

    if isinstance(directory, Catalogue):
        ctx.storage.save_catalogue(directory)


@cli.command()
@click.argument("name")
@click.pass_obj
def delete_catalogue(ctx: Context, name):
    """
    Deletes a catalogue. No files are affected.
    """
    existing_catalogue = ctx.storage.load_catalogue(name)

    if not existing_catalogue:
        raise click.BadParameter(f'Catalogue "{name}" not found')

    console.warning(
        f'Are you sure to delete the catalogue "{name}" pointing to "{existing_catalogue.path}"?'
        f"\nNote: No actual files will be affected."
    )
    if ctx.interactive and not Confirm.ask(f"Do you want to proceed?"):
        return

    ctx.storage.delete_catalogue(name)


@cli.command()
@click.argument("name")
@click.argument("src", required=False)
@click.option("--format-pattern", help='Pattern template. e.g. %Y/%m/{file}', required=False)
@click.option("--unknown-format-pattern", help='Pattern template fallback when date cannot get extracted', required=False)
@click.pass_obj
def create_catalogue(ctx: Context, name, src, format_pattern, unknown_format_pattern):
    """
    Creates a new catalogue.
    """
    src_path = None
    if src:
        with suppress(FileNotFoundError):
            src_path = Path(src).expanduser().resolve(strict=True)
        if not src_path or not src_path.is_dir():
            raise click.BadParameter(f'Error "{src}" is not an existing path')

    format_pattern = format_pattern or ctx.global_settings.format_pattern
    unknown_format_pattern = unknown_format_pattern or ctx.global_settings.unknown_format_pattern
    if not format_pattern:
        raise click.BadParameter(
            'Error there is no format pattern specified'
        )

    catalogue_path = src_path or ctx.workdir
    existing_catalogue = ctx.storage.load_catalogue(name)

    if existing_catalogue:
        raise click.BadParameter(
            f'There is already a catalogue named "{name}" pointing to "{existing_catalogue.path}"'
        )

    new_catalogue = Catalogue(
        name=name,
        format_pattern=format_pattern,
        unknown_format_pattern=unknown_format_pattern,
        path=catalogue_path,
    )
    new_catalogue.explore()

    files = new_catalogue.files
    if files:
        duplicated_files = new_catalogue.detect_duplicates()
        with console.status(
            "[green]Preparing summary...",
        ):
            print_table_summary(
                name=new_catalogue.name, files=files, duplicated_files=duplicated_files
            )

    console.print(
        f"Catalogue name: [bold purple]{name}[/]\n"
        f"Catalogue location: [bold purple]{catalogue_path}[/]\n"
        f"format_pattern: [bold purple]{new_catalogue.format_pattern}[/]\n"
        f"unknown_format_pattern: [bold purple]{new_catalogue.unknown_format_pattern}[/]\n"
    )
    ctx.storage.save_catalogue(new_catalogue)


@cli.command()
@click.argument("src")
@click.argument("dst")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def copy(ctx: Context, src, dst, dry_run):
    """
    Copy files. In case of duplicates will take the shortest name.
    """
    operation_mode = Operation.COPY
    return operate(ctx, src, dst, operation_mode, dry_run)


@cli.command()
@click.argument("src")
@click.argument("dst")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def move(ctx: Context, src, dst, dry_run):
    """
    Move files. In case of duplicates will take the shortest name.
    """
    operation_mode = Operation.MOVE
    return operate(ctx, src, dst, operation_mode, dry_run)


@cli.command()
@click.argument("src")
@click.argument("dst", required=False)
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def delete_duplicates(ctx: Context, src, dst, dry_run):
    """
    Delete duplicates.
    """
    operation_mode = Operation.DELETE
    return operate(ctx, src, dst, operation_mode, dry_run)


def filter_list_of_duplicated_files(
    duplicated_list_of_files_sorted_by_name_length, files_to_process
):
    """
    Returns a list of duplicates files which have different names and will be processed.
    """
    def has_different_names(files):
        return len(set([file.path.name for file in files])) > 1

    def at_least_one_file_is_going_to_be_process(files):
        return bool([file for file in files if file in files_to_process])

    return list(
        filter(
            lambda files: has_different_names(files)
            and at_least_one_file_is_going_to_be_process(files),
            duplicated_list_of_files_sorted_by_name_length,
        )
    )


def extract_files(src_data):
    duplicated_discarded_files = set()
    duplicated_list_of_files_sorted_by_name_length = []

    if isinstance(src_data, File):
        files_to_operate = [src_data]
    else:  # elif isinstance(src_data, (Catalogue, Directory)):
        duplicated_list_of_files = src_data.detect_duplicates()

        if duplicated_list_of_files:
            duplicated_list_of_files_sorted_by_name_length = list(
                sorted(duplicated_list, key=lambda file: (len(file.path.name), len(str(file.path))))
                for duplicated_list in duplicated_list_of_files
            )

            # Remove each first file from the duplicated list
            duplicated_discarded_files = set(
                chain(
                    *[
                        files[1:]
                        for files in duplicated_list_of_files_sorted_by_name_length
                    ]
                )
            )
        # ignore the duplicated_discarded_files since processing just one of them is enough
        files_to_operate = [
            file
            for file in src_data.files
            if file.is_media_type() and file not in duplicated_discarded_files
        ]
    return (
        duplicated_list_of_files_sorted_by_name_length,
        duplicated_discarded_files,
        files_to_operate,
    )


def get_from_input(ctx, value):
    """
    Catalogue > Directory > File > None
    """
    if not value:
        return None

    catalogue = ctx.storage.load_catalogue(value)
    if catalogue:
        return catalogue

    try:
        path = Path(value).expanduser().resolve(strict=True)
    except FileNotFoundError:
        raise click.BadParameter(
            f'Error "{value}" is neither a catalogue or an existing path'
        )

    if path.is_dir():
        return Directory.from_path(path)
    return File(path)


def operate(ctx, src, dst, operation_mode, dry_run=False):
    start_dt = datetime.now(timezone.utc)

    src_data = get_from_input(ctx, src)
    if not src_data:
        raise click.BadParameter(
            f'Error "{src}" is neither a catalogue or a valid path'
        )

    dst_data = get_from_input(ctx, dst)
    if dst_data and isinstance(dst_data, File):
        raise click.BadParameter(
            f'Error "{dst}" is neither a catalogue or an existing directory'
        )

    if isinstance(src_data, (Catalogue, Directory)) and dst_data:
        if src_data.path.is_relative_to(dst_data.path):
            raise click.BadParameter(
                f'Error "{dst}" cannot be a subdirectory of {src}'
            )

    if operation_mode in (Operation.MOVE, Operation.COPY):
        format_pattern = ctx.global_settings.format_pattern
        if dst_data and isinstance(dst_data, Catalogue):
            format_pattern = format_pattern or dst_data.format_pattern
        if not format_pattern:
            raise click.BadParameter(
                'Error there is no format pattern specified'
            )

    if isinstance(src_data, File) and not dst_data:
        raise click.BadParameter(
            f'Error "{src}" is a file but no valid destination was provided'
        )

    with console.status(
        f"[green]Inspecting files...",
    ):
        (
            duplicated_list_of_files_sorted_by_name_length,
            duplicated_discarded_files,
            files_to_operate,
        ) = extract_files(src_data)

    if operation_mode == Operation.DELETE:
        if dst_data:
            duplicate_files_across_directories = [
                file
                for file_list in dst_data.detect_duplicates_with(files_to_operate)
                for file in file_list
            ]
            # delete only dst files (which are reported as duplicated)
            files_to_process = list(
                filter(
                    lambda file: file.path.is_relative_to(dst_data.path),
                    duplicate_files_across_directories,
                )
            )
        else:  # files to delete are src duplicates
            files_to_process = [
                file for file in duplicated_discarded_files if file.is_media_type()
            ]

            duplicated_list_of_different_filenames = filter_list_of_duplicated_files(
                duplicated_list_of_files_sorted_by_name_length,
                files_to_process=files_to_process,
            )
            if duplicated_list_of_different_filenames:
                console.warning(
                    "I will keep the shortest name for each of the following groups:"
                )
                print_duplicate_files(
                    duplicated_files=duplicated_list_of_different_filenames
                )

    else:  # dst_data can only be Directory or Catalogue
        duplicate_files_across_directories = [
            file
            for file_list in dst_data.detect_duplicates_with(files_to_operate)
            for file in file_list
        ]

        files_to_process = set(files_to_operate) - set(
            duplicate_files_across_directories
        )
        duplicated_list_of_different_filenames_to_import = (
            filter_list_of_duplicated_files(
                duplicated_list_of_files_sorted_by_name_length,
                files_to_process=files_to_process,
            )
        )
        if duplicated_list_of_different_filenames_to_import:
            console.warning(
                "The files you attempt to import contain duplicates with different names.\n"
                "I will use the shortest name for each of the following groups:"
            )
            print_duplicate_files(
                duplicated_files=duplicated_list_of_different_filenames_to_import
            )

    console.info(f"Detected {len(files_to_process)} files.")
    if dry_run:
        console.warning(f"Running in dry-run, so no changes will be effective.")
    if (
        files_to_process
        and ctx.interactive
        and not Confirm.ask(f"Do you want to proceed to {operation_mode} these files?")
    ):
        return

    # actual processing
    tree, skipped_tree = process_files(
        ctx, src_data, dst_data, files_to_process, operation_mode, start_dt, dry_run
    )

    if dst_data:
        tree_starting_path = dst_data.path
    else:
        tree_starting_path = src_data.path

    guide_style = "bold bright_blue"
    if operation_mode == Operation.DELETE:
        guide_style = "bold green"
    rendered_tree = tree.generate_tree(tree_starting_path, guide_style=guide_style)
    if rendered_tree:
        console.print(f"\n{operation_mode.value.title()} {tree.file_count} files:")
        console.print(rendered_tree)

    rendered_skipped_tree = skipped_tree.generate_tree(
        src_data.path, guide_style="bold bright_black"
    )
    if rendered_skipped_tree:
        console.print(
            f"\n:warning: {skipped_tree.file_count} files have not being processed:"
        )
        console.print(rendered_skipped_tree)

    # save catalogues
    if isinstance(src_data, Catalogue) and not dry_run:
        ctx.storage.save_catalogue(src_data)
    if isinstance(dst_data, Catalogue) and not dry_run:
        ctx.storage.save_catalogue(dst_data)


def process_files(
    ctx, src_data, dst_data, files_to_process, operation_mode, start_dt, dry_run
):
    path_format = ctx.global_settings.format_pattern
    unknown_format_pattern = ctx.global_settings.unknown_format_pattern
    if isinstance(dst_data, Catalogue):
        path_format = path_format or dst_data.format_pattern
        unknown_format_pattern = unknown_format_pattern or dst_data.unknown_format_pattern

    tree = DirectoryTree()
    skipped_tree = DirectoryTree()

    with console.status(
        f"[green]Processing files...",
    ) as status:
        for file in files_to_process:
            status.update(
                status=f"[green]Processing file {tree.file_count} of {len(files_to_process)}"
            )
            dst_file_path = None
            old_path = file.path

            if operation_mode != Operation.DELETE:
                new_filename = generate_filename(
                    file,
                    src_data,
                    unknown_format_pattern=unknown_format_pattern,
                    path_format=path_format,
                    import_dt=start_dt,
                )
                if not new_filename:
                    skipped_tree.add_imported_file(file, old_path=file.path)
                    continue

                dst_file_path = dst_data.path.joinpath(new_filename)

            processed_file = process_file(
                file,
                dst_file_path,
                operation=operation_mode,
                dst_directory=dst_data,
                dry_run=dry_run,
            )

            tree.add_imported_file(processed_file, old_path=old_path)
    return tree, skipped_tree


def process_file(file, dst_file_path, operation, dst_directory, dry_run):
    logging.debug(f"{file.path} -> {dst_file_path}")

    if operation == Operation.DELETE:
        if not dry_run:
            file.delete()
        return file

    path_available = dst_directory.is_path_available(dst_file_path)
    if not path_available:
        logging.debug(f"Path {dst_file_path} not available, renaming file")
        dst_file_path = dst_directory.find_new_path(dst_file_path)

    if dry_run:
        file._path = dst_file_path
        return file

    if not dst_file_path.parent.exists():
        logging.debug(f'Creating folder "{dst_file_path.parent}"')
        dst_file_path.parent.mkdir(parents=True)

    if operation == Operation.MOVE:
        file.move_file(dst_file_path)
        dst_directory.add_file(file)
        return file

    if operation == Operation.COPY:
        new_file = file.clone_file(dst_file_path)
        dst_directory.add_file(new_file)
        return new_file


if __name__ == "__main__":
    cli()
