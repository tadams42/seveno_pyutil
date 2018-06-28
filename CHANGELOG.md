# Changelog

## 0.4.2 (2018-06-28)

* Added `in_batches` function

## 0.4.1 (2018-06-26)

* silent_remove now removes directories too.

## 0.4.0 (2018-06-20)

* Converted logging utilities SQLFormatter-s into SQLFilter-s.
* Added single line formatters to logging utilties

## 0.3.2 (2018-03-29)

* Implemented Stopwatch context manager

## 0.3.1 (2018-03-28)

* is_blank now works for empty lists, numbers, etc...

## 0.3.0 (2018-03-27)

* changed logging_utilities.DynamicContextFormatter -> logging_utilities.DynamicContextFilter

## 0.2.11 (2018-03-23)

* small fixes

## 0.2.10 (2018-03-23)

* small fixes

## 0.2.9 (2018-03-23)

* small fixes

## 0.2.8 (2018-03-23)

* small fixes

## 0.2.7 (2018-01-15)

* logging_utilities now transparently supports SQLAlchemy and optional coloring of HTTP logs

## 0.2.6 (2017-11-23)

* model_utilities.Representable is now customizable using private class attrs.

## 0.2.5 (2017-11-16)

* Added file_utilities.switch_extension

## 0.2.4 (2017-11-16)

* Added file_utilities.silent_remove

## 0.2.3 (2017-11-04)

* Added all_subclasses function

## 0.2.2 (2017-10-25)

* Added backports of Python 3.4 `min` and `max`.

## 0.2.1 (2017-10-24)

* Added logging_utilities.log_to_console_for

## 0.2.0 (2017-10-06)

* Added SQL log coloring formatter (for Django logs)

## 0.1.1 (2017-10-02)

* DynamicContextFormatter now keeps context in thread local.

## 0.1.0 (2017-09-26)

* Initial release
