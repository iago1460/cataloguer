import hashlib
import logging
import os
import shutil

from catalogue.const import Operation


def _move(src, dst, operation):
    logging.info(f'{src} -> {dst}/{src.name}')
    if operation == Operation.DRY_RUN:
        print(f'dry-run: {src} -> {dst}/{src.name}')
    elif operation == Operation.MOVE:
        shutil.move(str(src), dst.joinpath(src.name))
    elif operation == Operation.COPY:
        shutil.copy2(src, dst)


def move_file(file_path, dst_folder, operation):
    if not dst_folder.exists():
        logging.info(f'Creating folder "{dst_folder}"')
        if operation != Operation.DRY_RUN:
            os.makedirs(dst_folder)
    _move(file_path, dst_folder, operation)


def _chunk_reader(fobj, chunk_size=1024):
    """Generator that reads a file in chunks of bytes"""
    while True:
        chunk = fobj.read(chunk_size)
        if not chunk:
            return
        yield chunk


def _get_hash(filename, first_chunk_only=False):
    hashobj = hashlib.sha1()
    file_object = open(filename, 'rb')

    if first_chunk_only:
        hashobj.update(file_object.read(1024))
    else:
        for chunk in _chunk_reader(file_object):
            hashobj.update(chunk)
    hashed = hashobj.digest()

    file_object.close()
    return hashed


def get_files_and_size(path):

    files = set()
    hashes_by_size = {}
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            files.add(full_path)
            try:
                # if the target is a symlink (soft one), this will
                # dereference it - change the value to the actual target file
                full_path = os.path.realpath(full_path)
                file_size = os.path.getsize(full_path)
            except OSError as e:
                # not accessible (permissions, etc) - pass on
                logging.warning('Cannot read %s, %s', full_path, e)
                continue

            hashes_by_size.setdefault(file_size, []).append(full_path)
    return files, hashes_by_size


def get_file_duplicates(*hashes_by_size_list):
    hashes_on_1k = {}
    hashes_full = {}
    duplicates = {}

    hashes_by_size = {}
    for hashes in hashes_by_size_list:
        for file_size, file_paths in hashes.items():
            hashes_by_size.setdefault(file_size, []).extend(file_paths)

    # For all files with the same file size, get their hash on the 1st 1024 bytes
    for __, files in hashes_by_size.items():
        if len(files) < 2:
            continue  # this file size is unique, no need to spend cpy cycles on it

        for filename in files:
            try:
                small_hash = _get_hash(filename, first_chunk_only=True)
            except (OSError,):
                # the file access might've changed till the exec point got here
                continue

            hashes_on_1k.setdefault(small_hash, []).append(filename)

    # For all files with the hash on the 1st 1024 bytes, get their hash on the full file - collisions will be duplicates
    for __, files in hashes_on_1k.items():
        if len(files) < 2:
            continue  # this hash of fist 1k file bytes is unique, no need to spend cpy cycles on it

        for filename in files:
            try:
                full_hash = _get_hash(filename, first_chunk_only=False)
            except (OSError,):
                # the file access might've changed till the exec point got here
                continue

            duplicate = hashes_full.get(full_hash)
            if duplicate:
                duplicates.setdefault(full_hash, [duplicate]).append(filename)
            else:
                hashes_full[full_hash] = filename
    return duplicates
