from datetime import datetime

import argparse
import logging
import sys
import progressbar
from argparse import RawTextHelpFormatter
from pathlib import Path

from itertools import chain
from catalogue import __version__
from catalogue.const import Operation
from catalogue.model import Catalogue

progressbar.streams.wrap_stderr()
FORMAT = "%(asctime)s %(levelname)s : %(message)s"
DATEFMT = "%Y-%m-%d %H:%M:%S"
VIDEO_FOLDER_NAME = "videos"
KEEP_PARENT_FOLDERS = (
    "Time Lapse",
    "Burst Sequence",
)


def PathType(path):
    if path:
        return Path(path).resolve(strict=True)
    return None


def main():
    parser = argparse.ArgumentParser(
        formatter_class=RawTextHelpFormatter,
        description="Organize your photos folder,.\n"
        "Example usage:\n"
        "catalogue --src ./import_folder --dst ./my_catalogue --operation copy --verbose",
    )
    parser.add_argument(
        "--version",
        help="Displays version",
        dest="version",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--verbose",
        help='Makes verbose during the operation. Useful for debugging and seeing what is going on "under the hood".',
        dest="verbose",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--operation",
        help="Specify how to move files (copy, move or dry-run)",
        dest="operation",
        type=Operation,
        choices=list(Operation),
        required=False,
        default=Operation.DRY_RUN,
    )
    parser.add_argument(
        "--src",
        help="Path to the source directory.",
        dest="src_path",
        type=PathType,
        required=False,
        default=Path("."),
    )
    parser.add_argument(
        "--dst",
        help="Path to the destination directory.",
        dest="dst_path",
        type=PathType,
        required=False,
        default=None,
    )
    parser.add_argument(
        "--unknown-folder",
        help="If provided will be used for media without creation date\n"
        "It accepts same options as the format flag, strftime format will refer to current time",
        dest="unknown_folder",
        type=str,
        required=False,
        default=None,
    )
    parser.add_argument(
        "--format",
        help="Customize how to structure the files in your catalogue. e.g: '%%Y/%%m/%%d/{filename}\n"
        "All python strftime format codes are supported as well as {filename}, {basename}, {filename_extension}, {media_type}",
        dest="path_format",
        type=str,
        required=False,
        default="%Y/%m/%d/{filename}",
    )

    args = parser.parse_args()
    start_dt = datetime.now()

    if args.version:
        print(f"Version {__version__}")
        return

    logging_level = logging.INFO
    if args.verbose:
        logging_level = logging.DEBUG
    logging.basicConfig(
        format=FORMAT, datefmt=DATEFMT, stream=sys.stdout, level=logging_level
    )

    print("Scanning files...")
    src_catalogue = Catalogue.load(args.src_path)
    dst_catalogue = None
    if args.dst_path:
        dst_catalogue = Catalogue.load(args.dst_path)

    print("Checking duplicates...")

    duplicated_files_list = []
    if dst_catalogue is not None:
        duplicated_files_list = src_catalogue.detect_duplicates_with(dst_catalogue)

    if duplicated_files_list:
        print(f"Ignoring some duplicates files which are already present")
        if args.verbose:
            for files_list in duplicated_files_list:
                print(
                    "  * {files}".format(
                        files=", ".join(sorted(map(escape, files_list)))
                    )
                )
    duplicated_files = set(chain(*duplicated_files_list))

    duplicated_list_of_files_to_import = src_catalogue.detect_duplicates()
    if duplicated_list_of_files_to_import:
        duplicate_count = sum(
            (len(files) for files in duplicated_list_of_files_to_import)
        )
        print(
            f"Detected {duplicate_count} duplicate files to import, will import just one copy:"
        )
        for files_list in duplicated_list_of_files_to_import:
            print(
                "  * {files}".format(files=", ".join(sorted(map(escape, files_list))))
            )
        # Remove each first file from the list so it gets imported
        duplicated_list_of_files_to_import = set(
            chain(*[files[1:] for files in duplicated_list_of_files_to_import])
        )

    if not dst_catalogue:
        logging.info(f"Detected {len(src_catalogue.files)} files:")
        for file in src_catalogue.files:
            created = file.get_creation_date()
            if not file.is_media_type():
                logging.debug(f"Ignoring {file.get_media_type()} file {file.path} ")
            elif not created:
                logging.warning(f"Could not get creation date for {file.path}")
            else:
                logging.info(f"{file.path} created on {created}")

    imported_files = []
    if dst_catalogue:
        logging.info(f"Processing {len(src_catalogue.files)} files:")
        files = src_catalogue.files
        for file in progressbar.progressbar(files, redirect_stdout=True):
            if file.is_media_type():
                if (
                    file in duplicated_files
                    or file in duplicated_list_of_files_to_import
                ):
                    logging.debug(f"Skipping duplicated file {file.path}")
                    continue
                created = file.get_creation_date()
                parent_folder = keep_parent_folder(file.path)
                media_type = file.get_media_type()
                if not created:
                    logging.warning(f"Could not get creation date for {file.path}")
                    if args.unknown_folder:
                        new_filename = generate_filename(
                            file,
                            args.unknown_folder,
                            dt=start_dt,
                            parent_folder=parent_folder,
                            media_type=media_type,
                        )
                        dst_file_path = args.dst_path.joinpath(new_filename)

                        processed_file = process_file(
                            file, args.operation, dst_catalogue, dst_file_path
                        )
                        imported_files.append(processed_file)
                else:
                    new_filename = generate_filename(
                        file,
                        args.path_format,
                        dt=created,
                        parent_folder=parent_folder,
                        media_type=media_type,
                    )
                    dst_file_path = args.dst_path.joinpath(new_filename)

                    processed_file = process_file(
                        file, args.operation, dst_catalogue, dst_file_path
                    )
                    imported_files.append(processed_file)
        logging.info("Saving catalogue...")
        dst_catalogue.save_db()

    logging.info("Report:")
    logging.info(f"{len(imported_files)} files imported.")
    if args.verbose:
        for file in imported_files:
            logging.info(file)


def generate_filename(file, path_format, dt, parent_folder, media_type):
    basename, filename_extension = file.split_extension()
    filename = Path(parent_folder or "").joinpath(file.path.name)
    strftime_format = path_format.format(
        filename=filename,
        filename_extension=filename_extension,
        basename=basename,
        media_type=media_type,
    )
    return dt.strftime(strftime_format)


def process_file(file, operation, dst_catalogue, dst_file_path):
    path_available = dst_catalogue.is_path_available(dst_file_path)
    if not path_available:
        dst_file_path = dst_catalogue.find_new_path(dst_file_path)

    if operation == Operation.DRY_RUN:
        file.path = dst_file_path
        dst_catalogue.add_file(file)
        if path_available:
            logging.info(f"dry-run: {file.path} -> {dst_file_path}")
        else:
            logging.warning(f"dry-run: {file.path} -> {dst_file_path}")
        return None

    if operation == Operation.COPY:
        new_file = file.clone_file(dst_file_path)
        dst_catalogue.add_file(new_file)
        return new_file
    elif operation == Operation.MOVE:
        file.move_file(dst_catalogue)
        dst_catalogue.add_file(file)
        return file


def escape(file):
    return str(file).replace(" ", "\ ").replace("(", "\(").replace(")", "\)")


def keep_parent_folder(path) -> str:
    parent_folder = path.parent.name
    if any(map(lambda pattern: parent_folder.startswith(pattern), KEEP_PARENT_FOLDERS)):
        return parent_folder
    return ""


if __name__ == "__main__":
    main()
