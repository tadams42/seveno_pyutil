Examples and feature higlights
==============================

Stopwatch context manager
-------------------------

Simply measuring duration of code block

.. code-block:: python

    import time
    from seveno_pyutil import Stopwatch

    with Stopwatch() as stopwatch:
        # do some stuff
        time.sleep(0.1)

    print("%.2f ms" % stopwatch.duration_ms)
    # 100.22 ms

Inverting a dict
----------------

.. code-block:: python

    from seveno_pyutil import inverted

    d = {'a': 1, 'b': 2}
    inverted(d)
    # => {1: 'a', 2: 'b'}

Generating file checksum
------------------------

.. code-block:: python

    import hashlib
    from seveno_pyutil import file_checksum

    file_checksum('/tmp/foo.bar', hashlib.md5)
    # => '183590151a8af34e39e8e35351bfb470'

Silently creating directories
-----------------------------

It doesn't rise if path already exists:

.. code-block:: python

    import os
    from seveno_pyutil import silent_create_dirs

    silent_create_dirs('/tmp/foo/bar/baz/')
    os.path.exists('/tmp/foo/bar/baz/')
    # => True

    risen = False
    try:
        silent_create_dirs('/tmp/foo/bar')
    except OSError:
        risen = True

    risen
    # => False

But it doesn't block other exceptions:

.. code-block:: python

    silent_create_dirs('/usr/bin/foo')
    # => PermissionError: [Errno 13] Permission denied: '/usr/bin/foo'

    from seveno_pyutil import (file_checksum, silent_create_dirs,
        abspath_if_relative, silent_remove, switch_extension)

Silently removing files and directories
---------------------------------------

.. code-block:: python

    import os
    from seveno_pyutil import silent_remove, silent_create_dirs

    silent_create_dirs('/tmp/foo/bar/baz/')
    os.path.exists('/tmp/foo/bar/baz/')
    # => True

    silent_remove('/tmp/foo')
    os.path.exists('/tmp/foo/bar/baz/')
    # => False

    risen = False
    try:
        silent_remove('/tmp/foo')
    except OSError:
        risen = True

    risen
    # => False

But it doesn't block other exceptions:

.. code-block:: python

    silent_remove('/usr/bin')
    # PermissionError: [Errno 13] Permission denied: 'pv'

Forcing logs to always emmit single line of text + optionally colored logs
--------------------------------------------------------------------------

.. code-block:: python

    import logging
    from logging.config import dictConfig

    dictConfig({
        'version': 1,
        'formatters': {
            'syslog': {
                '()': 'seveno_pyutil.SingleLineFormatter',
                'format': '[%(levelname)s] %(message)s'
            },
            'console': {
                '()': 'seveno_pyutil.SingleLineColoredFormatter',
                'format': '[%(log_color)s%(levelname)s%(reset)s] %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',
                'formatter': 'console',
                'stream': 'ext://sys.stdout'
            },
            'syslog': {
                'class': 'logging.handlers.SysLogHandler',
                'level': 'DEBUG',
                'formatter': 'syslog',
                'address': ['127.0.0.1', 514],
                'facility': 'local1',
                'socktype': 'ext://socket.SOCK_DGRAM'
            }
        },
        'loggers': {
            'foobar': {
                'level': 'DEBUG',
                'handlers': ['console', 'syslog']
            }
        }
    })

    logger = logging.getLogger('foobar')

    try:
        raise RuntimeError('ZOMG!')

    except RuntimeError:
        logger.debug("Wat?", exc_info=True)

Which will emmit this to syslog::

    Jun 26 11:10:11 localhost  [DEBUG] Wat?\nTraceback (most recent call last):\n  File "<ipython-input-2-cd7145398458>", line 2, in <module>\n    raise RuntimeError('ZOMG!')\nRuntimeError: ZOMG!

And this to console::

    [DEBUG] Wat?\nTraceback (most recent call last):\n  File "<ipython-input-2-cd7145398458>", line 2, in <module>\n    raise RuntimeError('ZOMG!')\nRuntimeError: ZOMG!

Testing if we are dealing with blank data
-----------------------------------------

.. code-block:: python

    from seveno_pyutil import is_blank

    is_blank(None)
    # => True

    is_blank("")
    # => True

    is_blank("  \t  \r \r\n \n    ")
    # => True

    is_blank([])
    # => True

    is_blank(0)
    # => True

    is_blank(1)
    # => False

    is_blank("Foo")
    # => False

    is_blank("42")
    # => False

    is_blank("0")
    # => False

Processing iterable in batches
------------------------------

.. code-block:: python

    from functools import partial
    import random
    import time
    import threading

    from seveno_pyutil import in_batches

    def process_item(foo):
        time.sleep(random.random() * 0.5)
        print(foo)

    for batch in in_batches(range(42), of_size=5):
        workers = [
            threading.Thread(target=partial(process_item, itm))
            for itm in batch
        ]

        for worker in workers:
            worker.start()

        for worker in workers:
            worker.join()

        print("batch %s done" % batch)


Iterating over range of year months
-----------------------------------

.. code-block:: python

    from datetime import date
    from seveno_pyutil import iter_year_month

    for _ in iter_year_month(
        date(2022, 10, 13), date(2023, 4, 17)
    ):
        print(_)

    # 2022-11-01
    # 2022-12-01
    # 2023-01-01
    # 2023-02-01
    # 2023-03-01
