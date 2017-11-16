from seveno_pyutil.file_utilities import switch_extension


class describe_switch_extension(object):
    def it_returns_file_path_with_new_file_extension(self):
        assert switch_extension('/foo/bar/baz.txt', 'rtf') == '/foo/bar/baz.rtf'
        assert switch_extension('/foo/bar/baz.txt', '.rtf') == '/foo/bar/baz.rtf'

    def it_returns_same_file_path_if_given_extension_is_empty(self):
        assert switch_extension('/foo/bar/baz.txt', '') == '/foo/bar/baz.txt'
