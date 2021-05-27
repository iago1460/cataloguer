# Media cataloguer

Organize automatically your media files.

Move or copy your files according to your preferred format, using any combination of:
* Exif Creation date
* MIME type
* Filename
* Filename extension

### Usage

```bash
$ catalogue --help
usage: catalogue [-h] [--version] [--verbose] [--operation {move,copy,dry-run}]
               [--src SRC_PATH] [--dst DST_PATH] [--format PATH_FORMAT]
               [--unknown-folder UNKNOWN_FOLDER]

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
  --format PATH_FORMAT  Customize how to structure the files in your catalogue. By default : '%Y/%m/%d/{filename}
                        All python strftime format codes are supported as well as {filename}, {basename}, {filename_extension}, {media_type}
  --unknown-folder UNKNOWN_FOLDER
                        If provided will be used for media without creation date
                        It accepts same options as the format argument, strftime format codes will refer to current time instead of creation date
```

## Requirements
- Python 3.9 or Docker


## Installation

The easier way to run this project is using docker: 


### Using docker

Run example; notice `source` and `my_catalogue` need to be replace with your destinations:

    docker run --rm -v $(pwd)/source:/input:ro -v $(pwd)/my_catalogue:/output iago1460/catalogue:1.2.6 --src /input --dst /output --operation copy


### In a virtual environment

    virtualenv venv
    source venv/bin/activate
    pip3 install https://github.com/iago1460/photo-cataloguer/archive/1.2.6.zip
    catalogue --help


## Practical examples

Copy the files creating folders depending on its creation date structured by year, month and day number:

    catalogue --src source --dst my_catalogue --format %Y/%m/%d/{filename} --operation copy


Copy files like before but also copies files with unknown creation dates to `wtf` folder with the current date:

    catalogue --src ./source --dst ./my_catalogue --format %Y/%m/%d/{filename} --unknown-folder ./my_catalogue/wtf/%Y_%m_%d/{filename} --operation copy


Detect duplicates in a given folder and list debugging data:

    catalogue --src ./source --verbose


If `operation` is not specified it will not affect any files, it's always a good idea to run it before hand.


## Features

* Move, Copy or Dry Run operation modes
* Obscure Creation date detection
* Custom folder structure definition
* Duplication detection
* Respect contents on destination folder
* Fast duplication detection

## TODO list

* Video support
* Push package to pip

