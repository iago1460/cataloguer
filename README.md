# Photo cataloguer

Organize automatically your media files.

Move or copy your files according to your preferred format, using any combination of:
    * Exif Creation date
    * MIME type
    * Filename
    * Filename extension

### Example: 

Copy the files to a given directory renaming these by its creation date
```
To use `catalogue --src input --dst output --operation copy --format %Y-%m-%dT%H:%M:%S{filename_extension}`
```

Copy the files creating folders depending of its creation date keeping the original filename
```
To use `catalogue --src input --dst output --operation copy --format %Y/%m/%d/{filename}`
```

### Usage

```bash
$ catalogue --help
usage: catalogue [-h] [--version] [--verbose]
                 [--operation {move,copy,dry-run}] [--src SRC_PATH]
                 [--dst DST_PATH] [--unknown-folder UNKNOWN_FOLDER]
                 [--format PATH_FORMAT]

Organize your photos folder,.
Example usage:
catalogue --src ./import_folder --dst ./my_catalogue --operation copy --verbose

optional arguments:
  -h, --help            show this help message and exit
  --version             Displays version
  --verbose             Makes verbose during the operation. Useful for debugging and seeing what is going on "under the hood".
  --operation {move,copy,dry-run}
                        Specify how to move files (copy, move or dry-run)
  --src SRC_PATH        Path to the source directory.
  --dst DST_PATH        Path to the destination directory.
  --unknown-folder UNKNOWN_FOLDER
                        If provided will be used for media without creation date
  --format PATH_FORMAT  Customize how to structure the files in your catalogue. e.g: '%Y/%m/%d/{filename}'
                        All python strftime format codes are supported as well as {filename}, {filename_extension}, {media_type}, {mime_type}
```

## Installation

    virtualenv venv
    source venv/bin/activate
    pip3 install https://github.com/iago1460/photo-cataloguer/archive/0.9.9.zip
    
    catalogue --help


## Features

* Move, Copy or Dry Run operation modes
* Scan for duplicates

## TODO list

* Push package to pip
* Video support
* Symlink between folder video and photo

