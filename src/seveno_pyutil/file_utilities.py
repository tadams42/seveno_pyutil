from __future__ import annotations

import shutil
from pathlib import Path

from .string_utilities import is_blank


def file_checksum(file_path: str | Path, hashlib_callable):
    """Given path of the file and hash function, calculates file digest"""

    if Path(file_path).is_file() and callable(hashlib_callable):
        hash_obj = hashlib_callable()
        with Path(file_path).open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    return None


def abspath_if_relative(relative_path: str | Path, relative_to: str | Path):
    """Creates absolute path from relative, but places it under other path.

    Example:
        >>> abspath_if_relative('foo/bar/baz', relative_to='/tmp')
        '/tmp/foo/bar/baz'
    """
    retv = relative_path

    if not is_blank(relative_path):
        if not is_blank(relative_to):
            if not Path(relative_path).is_absolute():
                retv = (Path(relative_to) / Path(relative_path)).resolve().absolute()
        else:
            retv = Path(relative_path).resolve().absolute()

    return retv


def move_and_create_dest(src_path: str | Path, dst_dir: str | Path):
    """
    Moves ``src_path`` to ``dst_dir`` directory.

    Expects ``dst_dir`` to be directory and if it doesn't exits, tries to
    create it.
    """
    Path(dst_dir).mkdir(parents=True, exist_ok=True)
    shutil.move(src_path, dst_dir)
    return Path(dst_dir) / Path(dst_dir).name
