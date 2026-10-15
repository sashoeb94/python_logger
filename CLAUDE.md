# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A small, generic Python 3 library for logging and exception handling: a `Logger` wrapper around the stdlib `logging` module that writes to stdout and routes caught exceptions to an optional user-supplied error handler. It requires Python 3.13+ and has no runtime dependencies. Email/Mailgun alerting was removed in the Python 3 port; don't reintroduce a hard dependency on any transport. Alerting belongs in the user's error handler.

## Commands

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
pytest                                                  # full suite (tests/)
pytest tests/test_logger.py::test_protect_method_bare   # single test
python example.py                                       # usage demo; README points here
```

There's no linter config. `example.py` covers every public feature and doubles as a smoke test; it makes no network calls.

When the public API changes, update all three: `example.py`, the README (usage snippet, the API section, and the migration notes if the change breaks callers), and this file.

## History

The library was ported from Python 2, where it was `app_logger.py` plus `email_config.py`, with Mailgun alerts sent through `requests` and `cgitb`. The port removed `send_alerts`, `is_service` and `instance` along with the email code. The README's "Migrating from the Python 2 version" section lists the changes for users who are upgrading.

## Architecture

- `python_logger/logger.py`: the whole library, in the `Logger` class. `python_logger/__init__.py` re-exports it.
  - `__init__` builds a fresh `logging.Logger` (not `logging.getLogger`, so it isn't registered globally and same-named instances don't share handlers) with a single stdout `StreamHandler`. It then binds `debug`/`info`/`warning`/`error`/`critical` straight onto the instance. `exception` is a custom method.
  - `log_level` accepts the string keys in `LOG_LEVELS` (case-insensitive) or a stdlib int level. An unknown string raises `ValueError`.
  - `exception(msg)` logs with stacktrace. If an error handler is set (the `error_handler=` constructor arg or `set_custom_error_handler`) **and** an exception is active, it calls `handler(traceback, sys.exc_info())`, where the first argument is the stdlib `traceback` module. That signature is kept for compatibility with the Python 2 version, which passed `cgitb.traceback`. Exceptions raised by the handler are logged, not propagated.
  - `protect_method` is a decorator (usable with or without arguments). It catches exceptions, routes them through `self.exception`, and returns `exception_response`.
  - Supports `with Logger(...) as LOGGER:`. `__exit__` doesn't suppress exceptions.
  - All state is per instance (`self._logger`, `self._error_handler`); `LOGGER` is a property that exposes the underlying `logging.Logger`.
- Tests use `capsys` to assert on stdout. That works because the `StreamHandler` binds `sys.stdout` at construction time, so a `Logger` must be created inside the test, not at module level.
