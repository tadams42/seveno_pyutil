import os
import pwd


def current_user_home():
    """Queries OS for path to current user home directory."""
    # ie. ~/.my_app.conf The following relies on shell environment and thus will
    # not work in any non-interactive non-login shells (ie. under supervisord)
    # os.path.expanduser('~/')
    # instead, use pwd (UID and unix password file) to decypher home dir
    return pwd.getpwuid(os.getuid()).pw_dir


def current_user():
    """Queries OS for current user username."""
    return pwd.getpwuid(os.getuid()).pw_name
