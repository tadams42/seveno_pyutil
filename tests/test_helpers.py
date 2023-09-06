from inspect import getsourcefile
from pathlib import Path

from faker import Faker

TEST_RESOURCES_ROOT = (
    (Path(getsourcefile(lambda: 0)) / ".." / "fixtures").resolve().absolute()
)

fake = Faker()
