import argparse
import logging
import sys
from argparse import RawTextHelpFormatter
from pathlib import Path

from catalogue import __version__
from catalogue.const import Operation
from catalogue.filesystem import move_file, get_file_duplicates, get_files_and_size
from catalogue.metadata import is_image, get_image_creation_date

FORMAT = '%(asctime)s %(levelname)s : %(message)s'
DATEFMT = '%Y-%m-%d %H:%M:%S'


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

    args = parser.parse_args()

    if args.version:
        print(f'Version {__version__}')
        return

    logging_level = logging.ERROR
    if args.verbose:
        logging_level = logging.DEBUG
    logging.basicConfig(format=FORMAT, datefmt=DATEFMT, stream=sys.stdout, level=logging_level)

    print('Checking for duplicates...')
    catalogue_files = set()
    catalogue_hashes = {}
    if args.dst_path:
        catalogue_files, catalogue_hashes = get_files_and_size(args.dst_path)

    src_files, src_hashes = get_files_and_size(args.src_path)
    duplicates = get_file_duplicates(catalogue_hashes, src_hashes)
    if duplicates:
        print('The following files are duplicated:')
        for files in duplicates.values():
            print('  * {files}'.format(files=', '.join(files)))
        print(f'Found {int(len(duplicates)/2)} duplicates')
    else:
        print('No duplicates found')

    file_collisions = []
    if args.dst_path:
        print('{operation} files...'.format(operation=str(args.operation).capitalize()))
        for path in args.src_path.rglob('**/*'):
            if is_image(path):
                created = get_image_creation_date(path)

                sub_path = Path('{year}/{month}/{day}'.format(year=created.year, month=created.month, day=created.day))
                dst_path = args.dst_path.joinpath(sub_path)
                dst_file_path = dst_path.joinpath(path.name)
                if str(dst_file_path) not in catalogue_files:
                    move_file(path, dst_path, operation=args.operation)
                    catalogue_files.add(str(dst_file_path))
                else:
                    file_collisions.append((path, dst_file_path))
    else:
        print('No destination folder provided')

    if file_collisions:
        print('The following files were already present in the catalogue:')
        for file, catalogue_file in file_collisions:
            print(f'  * {file} <-> {catalogue_file}')


if __name__ == '__main__':
    main()
