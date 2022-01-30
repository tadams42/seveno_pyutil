import errno
import os
import shutil

from .string_utilities import is_blank


def file_checksum(file_path, hash_callable):
    """Given path of the file and hash function, calculates file digest"""
    if os.path.isfile(file_path) and callable(hash_callable):
        hash_obj = hash_callable()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    return None


def silent_create_dirs(dir_path):
    """Tries to create directory and silently skips if it exists."""
    try:
        os.makedirs(os.path.abspath(dir_path))
    except OSError as exception:
        # We don't care if dir already exists
        if exception.errno != errno.EEXIST or (
            exception.errno == errno.EEXIST
            and not os.path.isdir(os.path.abspath(dir_path))
        ):
            raise


def abspath_if_relative(relative_path, relative_to):
    """Creates absolute path from relative, but places it under other path.

    Example:
        >>> abspath_if_relative('foo/bar/baz', relative_to='/tmp')
        '/tmp/foo/bar/baz'
    """
    retv = relative_path

    if not is_blank(relative_path):
        if not is_blank(relative_to):
            if not os.path.isabs(relative_path):
                retv = os.path.abspath(os.path.join(relative_to, relative_path))
        else:
            retv = os.path.abspath(relative_path)

    return retv


def move_and_create_dest(src_path, dst_dir):
    """
    Moves ``src_path`` to ``dst_dir`` directory.

    Expects ``dst_dir`` to be directory and if it doesn't exits, tries to
    create it.
    """
    silent_create_dirs(dst_dir)
    shutil.move(src_path, dst_dir)
    return os.path.join(dst_dir, os.path.basename(src_path))


def silent_remove(file_or_dir_path):
    """
    Deletes file or directory (even if not empty). Doesn't rise if it doesn't
    exist.
    """

    if is_blank(file_or_dir_path):
        return None

    try:
        if os.path.isdir(file_or_dir_path):
            shutil.rmtree(file_or_dir_path)
        else:
            os.remove(file_or_dir_path)

    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def switch_extension(file_path, new_extension):
    if is_blank(new_extension):
        return file_path

    if not new_extension.startswith("."):
        new_extension = "." + new_extension

    return os.path.join(
        os.path.dirname(file_path),
        os.path.splitext(os.path.basename(file_path))[0] + new_extension,
    )
