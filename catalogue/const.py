from enum import Enum


class Operation(Enum):
    MOVE = 'move'
    COPY = 'copy'
    DRY_RUN = 'dry-run'

    def __str__(self):
        return self.value
