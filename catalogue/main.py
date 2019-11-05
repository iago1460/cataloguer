import argparse
import logging
import sys
import magic
import progressbar
from argparse import RawTextHelpFormatter
from pathlib import Path

from itertools import chain
from catalogue import __version__
from catalogue.const import Operation
from catalogue.filesystem import process_file, get_file_duplicates, get_files_and_size, get_filename_extension
from catalogue.metadata import is_image, is_video, get_creation_date, get_media_type

progressbar.streams.wrap_stderr()
FORMAT = '%(asctime)s %(levelname)s : %(message)s'
DATEFMT = '%Y-%m-%d %H:%M:%S'
VIDEO_FOLDER_NAME = 'videos'
KEEP_PARENT_FOLDERS = (
    'Time Lapse',
    'Burst Sequence',
)


def PathType(path):
    if path:
        return Path(path).resolve(strict=True)
    return None


def main():
    parser = argparse.ArgumentParser(
        formatter_class=RawTextHelpFormatter,
        description=
        "Organize your photos folder,.\n"
        "Example usage:\n"
        "catalogue --src ./import_folder --dst ./my_catalogue --operation copy --verbose"
    )
    parser.add_argument(
        '--version',
        help='Displays version',
        dest='version',
        action='store_true',
        default=False
    )
    parser.add_argument(
        '--verbose',
        help='Makes verbose during the operation. Useful for debugging and seeing what is going on "under the hood".',
        dest='verbose',
        action='store_true',
        default=False
    )
    parser.add_argument(
        '--operation',
        help="Specify how to move files (copy, move or dry-run)",
        dest='operation',
        type=Operation,
        choices=list(Operation),
        required=False,
        default=Operation.DRY_RUN
    )
    parser.add_argument(
        '--src',
        help="Path to the source directory.",
        dest='src_path',
        type=PathType,
        required=False,
        default=Path('.')
    )
    parser.add_argument(
        '--dst',
        help="Path to the destination directory.",
        dest='dst_path',
        type=PathType,
        required=False,
        default=None
    )
    parser.add_argument(
        '--unknown-folder',
        help="If provided will be used for media without creation date",
        dest='unknown_folder',
        type=str,
        required=False,
        default=None
    )
    parser.add_argument(
        '--format',
        help=
        "Customize how to structure the files in your catalogue. e.g: '%%Y/%%m/%%d/{filename}'\n"
        "All python strftime format codes are supported as well as {filename}, {filename_extension}, {media_type}, {mime_type}",
        dest='path_format',
        type=str,
        required=False,
        default='%Y/%m/%d/{filename}'
    )

    args = parser.parse_args()

    if args.version:
        print(f'Version {__version__}')
        return

    logging_level = logging.WARNING
    if args.verbose:
        logging_level = logging.DEBUG
    logging.basicConfig(format=FORMAT, datefmt=DATEFMT, stream=sys.stdout, level=logging_level)

    print('Scanning files...')
    catalogue_files = set()
    catalogue_hashes = {}
    if args.dst_path:
        catalogue_files, catalogue_hashes = get_files_and_size(args.dst_path)
        catalogue_duplicates = get_file_duplicates(catalogue_hashes).values()
        if catalogue_duplicates:
            duplicate_count = sum((len(files) for files in catalogue_duplicates)) - len(catalogue_duplicates)
            print(f'Your catalogue contains {duplicate_count} duplicates:')
            for files in catalogue_duplicates:
                print('  * {files}'.format(files=', '.join(sorted(map(escape, files)))))

    src_files, src_hashes = get_files_and_size(args.src_path)
    src_duplicates = get_file_duplicates(src_hashes).values()
    if src_duplicates:
        duplicate_count = sum((len(files) for files in src_duplicates)) - len(src_duplicates)
        print(f'The following {duplicate_count} files to import are duplicated:')
        for files in src_duplicates:
            print('  * {files}'.format(files=', '.join(sorted(map(escape, files)))))
    duplicates_src = set(chain(*src_duplicates))

    duplicates_across = set()
    if args.dst_path:
        print('Checking duplicates across src and dst paths...')
        duplicates_across = set(chain(*get_file_duplicates(catalogue_hashes, src_hashes, diff=True).values()))

    skipped_files = []
    missing_creation_date_files = []
    conflicting_name_files = []
    imported_files = []
    if args.dst_path:
        print('{operation} files...'.format(operation=str(args.operation).capitalize()))
        for path in progressbar.progressbar(src_files, redirect_stdout=True):
            if path.is_file():
                mime_type = magic.from_file(str(path), mime=True)
                if not is_image(mime_type) and not is_video(mime_type):
                    continue
                media_type = get_media_type(mime_type)
                logging.debug(f'{mime_type} - {path}')
                created = get_creation_date(path, mime_type)
                parent_folder = keep_parent_folder(path)
                if not created:
                    logging.warning(f'Could not get creation date for {path}')
                    if args.unknown_folder:
                        dst_file_path = args.dst_path.joinpath(args.unknown_folder).joinpath(media_type).joinpath(path.name)
                        if path in duplicates_across:
                            skipped_files.append(path)
                        elif dst_file_path not in catalogue_files:
                            process_file(path, dst_file_path, operation=args.operation)
                            catalogue_files.add(dst_file_path)
                            missing_creation_date_files.append(path)
                        elif path in duplicates_src:
                            skipped_files.append(path)
                        else:
                            conflicting_name_files.append((path, dst_file_path))
                    else:
                        missing_creation_date_files.append(path)
                    continue

                filename_extension = get_filename_extension(path.name)
                filename = Path(parent_folder).joinpath(path.name)
                strftime_format = args.path_format.format(
                    filename=filename,
                    filename_extension=filename_extension,
                    mime_type=mime_type,
                    media_type=media_type,
                )
                sub_path = Path(created.strftime(strftime_format))
                dst_file_path = args.dst_path.joinpath(sub_path)

                if path in duplicates_across:
                    skipped_files.append(path)
                elif dst_file_path not in catalogue_files:
                    process_file(path, dst_file_path, operation=args.operation)
                    catalogue_files.add(dst_file_path)
                    imported_files.append(path)
                elif path in duplicates_src:
                    skipped_files.append(path)
                else:
                    conflicting_name_files.append((path, dst_file_path))

    else:
        print('No destination folder provided')

    if skipped_files:
        print(f'{len(skipped_files)} files were skipped, since they were already present in the catalogue.')
        if args.verbose:
            for file in skipped_files:
                print(f'  *  {escape(file)}')
    if missing_creation_date_files:
        if args.unknown_folder:
            print(f'{len(missing_creation_date_files)} files WITHOUT METADATA were imported into the "{args.unknown_folder}" folder:')
        else:
            print(f'{len(missing_creation_date_files)} files WITHOUT METADATA COULD NOT be imported:')
        for file in missing_creation_date_files:
            print(f'  * {escape(file)}')
    print(f'{len(imported_files) + len(missing_creation_date_files if args.unknown_folder else ())} files imported.')
    if conflicting_name_files:
        print(f'{len(conflicting_name_files)} files COULD NOT be imported:')
        for file, dst_file in conflicting_name_files:
            print(f'  * {escape(file)} != {escape(dst_file)}')


def escape(file):
    return str(file).replace(' ', '\ ').replace('(', '\(').replace(')', '\)')


def keep_parent_folder(path) -> str:
    parent_folder = path.parent.name
    if any(map(lambda pattern: parent_folder.startswith(pattern), KEEP_PARENT_FOLDERS)):
        return parent_folder
    return ''

if __name__ == '__main__':
    main()
