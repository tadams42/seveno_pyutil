# TODO

- Stopwatch doesn't work for async, document or fix or both
- clean logging_utilities: replace context manager with better one
- add SQLAlchemy extensions

- make logging context similar to one in filter_commander and investigate need
  for RFC syslog format

- refactor http logging into filter / formatter / adapter so that it can be used not in general logging config but in places like middlware where we want to adapt normal logger to emmit http messages formatted by our http logger
    - hmm, we want to be able to config this http logger like other ones - in logging config
    - thing to think about...
