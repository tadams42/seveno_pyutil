import os
from inspect import getsourcefile

import pytest
from faker import Faker

TEST_RESOURCES_ROOT = os.path.abspath(
    os.path.join(getsourcefile(lambda: 0), "..", "fixtures")
)

fake = Faker()
