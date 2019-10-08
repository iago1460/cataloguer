import argparse
import logging
import sys
from argparse import RawTextHelpFormatter
from pathlib import Path

from catalogue import __version__
from catalogue.const import Operation
from catalogue.filesystem import move_file, get_file_duplicates
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
        "python3 -m catalogue --src ./import_folder --dst ./my_catalogue --operation copy --verbose"
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
    duplicates = get_file_duplicates(list(filter(lambda x: bool(x), (args.src_path, args.dst_path))))
    if duplicates:
        print('The following files are duplicated:')
        for files in duplicates.values():
            print('  * {files}'.format(files=', '.join(files)))
        print(f'Found {int(len(duplicates)/2)} duplicates')
    else:
        print('No duplicates found')

    if args.dst_path:
        print('{operation} files...'.format(operation=str(args.operation).capitalize()))
        for path in args.src_path.rglob('**/*'):
            if is_image(path):
                created = get_image_creation_date(path)

                sub_path = Path('{year}/{month}/{day}'.format(year=created.year, month=created.month, day=created.day))
                dst_path = args.dst_path.joinpath(sub_path)
                move_file(path, dst_path, operation=args.operation)
    else:
        print('No destination folder provided')

if __name__ == '__main__':
    main()
