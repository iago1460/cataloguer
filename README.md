# Photo cataloguer

Organize automatically your photos by date.

Move/Copy your files to a file system catalogue order by its creation date `<year>/<month>/<day>`


```bash
$ python3 -m catalogue -h
usage: __main__.py [-h] [--verbose] [--operation {move,copy,dry-run}] --src
                   SRC_PATH [--dst DST_PATH]

Organize your photos folder,.
Example usage:
python3 -m catalogue --src ./import_folder --dst ./my_catalogue --operation copy --verbose

optional arguments:
  -h, --help            show this help message and exit
  --version             Displays version
  --verbose             Makes verbose during the operation. Useful for debugging and seeing what is going on "under the hood".
  --operation {move,copy,dry-run}
                        Specify how to move files (copy, move or dry-run)
  --src SRC_PATH        Path to the source directory.
  --dst DST_PATH        Path to the destination directory.
```

## Installation

    virtualenv venv
    source venv/bin/activate
    pip3 install https://github.com/iago1460/photo-cataloguer/archive/0.9.3.zip
    
    catalogue --help


## Features

* Move, Copy or Dry Run operation modes
* Scan for duplicates

## TODO list

* Push package to pip
* Video support
* Symlink between folder video and photo

