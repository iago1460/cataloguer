import json
import logging
from pathlib import Path

from pydantic import BaseModel

from .filesystem.directory import Catalogue

logger = logging.getLogger(__name__)


class Storage(BaseModel):
    path: Path

    def load_catalogue(self, name: str, force_reload=True):
        try:
            with open(self.path.joinpath(f"{name}.json"), "r") as fd:
                return Catalogue.parse_obj(json.load(fd), force_reload=force_reload)
        except FileNotFoundError:
            return None
        except Exception as exception:
            logger.warning(f'Error happen when loading "{name}": {exception}')
            return None

    def delete_catalogue(self, name: str):
        self.path.joinpath(f"{name}.json").unlink()

    def save_catalogue(self, catalogue: Catalogue):
        catalogue.save(self.path.joinpath(f"{catalogue.name}.json"))
