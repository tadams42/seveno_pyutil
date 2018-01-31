__version__ = '0.2.8'

import logging
import sys

from . import (datetime_utilities, dict_utilities, file_utilities,
               logging_utilities, metaprogramming_helpers, model_utilities,
               os_utilities, string_utilities)

if sys.version_info < (3, 4, 0):
    from .compatibility import py34_min as min
    from .compatibility import py34_max as max
else:
    min = min
    max = max

logging.getLogger(__name__).addHandler(logging.NullHandler())
