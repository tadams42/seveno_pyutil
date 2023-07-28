# Changelog

## 0.8.4 (2023-07-28)

- feat: removed SQL duration threshold warning
- feat: support logging of compiled SQL statements on psycopg3

## 0.8.4 (2023-07-26)

- fix: don't rely on json to be able to encode SQL parameters

## 0.8.3 (2023-06-26)

- build: added GitHub action for publishing releases to PyPi

## 0.8.2 (2023-06-07)

- feat: prettier format for multiline SQL in SQLFilter

## 0.8.1 (2023-06-07)

- feat: SQLFiler can now sometimes print real SQL instead of query string + params

## 0.8.0 (2023-02-24)

- feat: replaced logging formatters with `PrettyFormatter`
- feat: added `next_working_day()`
- feat: replaced dateutil timezones with `zoneinfo`
- chore: added some `typing` annotations

## 0.7.1 (2022-10-28)

- feat: prettier error log message in SQLFilter

## 0.7.0 (2022-09-02)

- feat: added `iter_year_month`
- switched from TravisCI -> GitHub actions

## 0.6.3 (2021-03-11)

- fix: SQL logs shortening is now configurable, for ultimate flexibility

## 0.6.2 (2021-03-11)

- fix: another try at SQL logging very long SQL statements and/or parameters

## 0.6.1 (2021-03-04)

- fix: prevented SQL logging from producing huge messages and crashing loggers

## 0.6.0 (2021-01-30)

- dropped support for Python < 3.9
- replaced pytz with stdlib zoneinfo
- switched to pyproject.toml

## 0.5.8 (2021-08-31)

- fix: `tzlocal` timezone object doesn't always have `localize()`

## 0.5.7 (2020-06-02)

- fix: SQLFilter was not logging debug level messages (SQL queries)

## 0.5.6 (2019-06-23)

- fix: SQL logging could sometimes generate messages that are too long for rsyslog
- dropped support for Python 3.5
- Added support for Python 3.8

## 0.5.5 (2019-05-20)

- minor fixes

## 0.5.4 (2019-05-16)

- Removed HTTP logging helpers and DynamicContextFilter
- SQLAlchemy logger can now optionally collect statistics

## 0.5.3 (2019-04-01)

- fixes bug in http logging utilities

## 0.5.2 (2019-03-13)

- removed xml_utilities
- removed model_utilities

## 0.5.1 (2019-01-18)

- small fixes

## 0.5.0 (2019-01-17)

- dropped support for Python versions < 3.5
- fixed small bugs
- added error_utilities
- added xml_utilities

## 0.4.3 (2018-09-26)

* Refactored and improved SQLAlchemy logging capabilities of SQLFilter
* Added JSONEncoderWithDateTime
* Added IsoTimeField
* Fixed problems with Validateable, renamed to ValidateableMixin
* Added 'import_string' - ripped from Django, need it elsewhere so like to have it independent of Django

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
