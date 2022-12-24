from .default_config import *

try:
    from .config import *  # pyright: ignore [reportMissingImports]
except ModuleNotFoundError:
    pass
