# Media cataloguer

Organize your media files using your preferred directory structure.

* Do you have pictures taken from different devices? 
* Do you want control over your file system?
* Do you wish to unify all your media files and remove duplicates?

If you reply affirmative to any of the previous questions, this tool could be right for you too.

This tool helps you to unify and organise your media files using your own rules. 
It also deals with duplicates, so you don't have to.


## Disclaimer

Per design this command line interface tool deletes only duplicate files to potentially avoid any risk of losing data.


## Features

* Move, Copy or delete duplicates operations
* User-friendly console output
* Obscure creation date detection
* Custom folder structure definition
* Duplication detection
* Does not alter existing files


## Requirements
- Python 3.9 or higher

## Installation

    pip install cataloguer


### Usage

```bash
$ cataloguer --help
                                                                                                                                                                                                    
 Usage: cataloguer [OPTIONS] COMMAND [ARGS]...                                                                                                                                                             
                                                                                                                                                                                                           
 Command line interface.                                                                                                                                                                                   
 All [OPTIONS] can be passed as environment variables with the "CATALOGUER_" prefix.                                                                                                                       
 file arguments accept file names and a special value "-" to indicate stdin or stdout                                                                                                                      
                                                                                                                                                                                                           
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --verbose                       -v        Enables verbose mode. Disabled by default                                                                                                                     │
│ --format-pattern                    TEXT  Pattern template. e.g. %Y/%m/{file}                                                                                                                           │
│ --unknown-format-pattern            TEXT  Pattern template fallback when date cannot get extracted                                                                                                      │
│ --interactive/--no-interactive            Disables confirmation prompts. Enabled by default                                                                                                             │
│ --help                                    Show this message and exit.                                                                                                                                   │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ copy                                          Copy files. In case of duplicates will take the shortest name.                                                                                            │
│ create-catalogue                              Creates a new catalogue.                                                                                                                                  │
│ delete-catalogue                              Deletes a catalogue. No files are affected.                                                                                                               │
│ delete-duplicates                             Delete duplicates.                                                                                                                                        │
│ inspect                                       Inspects a path or a catalogue                                                                                                                            │
│ move                                          Move files. In case of duplicates will take the shortest name.                                                                                            │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```


## Quickstart

We are going to start creating a new directory `media`:

    mkdir media

We are going to create a new catalogue named `local_photos` which is going to get store on the `media` directory.
We specify our format pattern so photos are group by `year` and a subgroup of `month`:

    cataloguer create-catalogue local_media ./media --format-pattern %Y/%m/{file}


Now, we add some photos from an old storage drive:

    cataloguer copy /mnt/hdd/old_photos local_media


Later on, we decided we want to reorganize our local home folder, but we are not sure of how many files are 
going to be affected, so we run the command in `dry-run` mode:

    cataloguer move ~/ local_media --dry-run

After seeing the output, we decided to just reorganize our `Pictures`:

    cataloguer move ~/Pictures/ local_media


To get a summary of our catalogue we run:

    cataloguer inspect local_media


## Options

`format-pattern` accepts the following patterns
* Common date codes:
  * `%d`: Day of the month as number
  * `%m`: Month as number
  * `%Y`: Year as number
  * `%A`: Weekday name 
  * `%B`: Month name
  * other format codes specified [here](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes)
* `/` Specifies a new folder
* `{media_type}`: File type (`image`, `video`)
* `{media_format}`: File format (`jpeg`, `tiff`, `png`, `gif`, `mp4` ...)
* `{file}` Original filename (`photo.jpg`)
* `{file_extension}` filename extension (`photo`)
* `{file_name}` filename without the extension (`jpg`)
* `{relative_path}` Relative path to the source directory


### Advance usage:
`unknown-format-pattern` Accepts the same variables as `format-pattern` but date patterns 
are resolved using the current date since it was not possible to recover the creation date of the file.
This can be useful to not leave files behind.

Variables can also be specified as environment variables, using a `CATALOGUER_` prefix. e.g: 

    export CATALOGUER_FORMAT_PATTERN=%Y/%m/{file}

`CATALOGUER_STORAGE_LOCATION` Accepts any path. That location will store cataloguer metadata.
By default, it will create a `.catalogues` in the user's home directory.

#### Examples:

Pattern to fix file extensions keeping the folder structure:

     cataloguer --format-pattern {relative_path}/{basename}.{media_format} move ./input ./output


## TODO list

* Video support
