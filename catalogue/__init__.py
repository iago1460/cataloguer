import sys

if sys.version_info < (3, 9):
    raise RuntimeError("Python 3.9 or later is required")

__version__ = "1.0"
