# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A small, generic Python 3 library for logging and exception handling: a `Logger` wrapper around the stdlib `logging` module that writes to stdout and routes caught exceptions to an optional user-supplied error handler. It requires Python 3.13+ and has no runtime dependencies. Email/Mailgun alerting was removed in the Python 3 port; don't reintroduce a hard dependency on any transport. Alerting belongs in the user's error handler.

## Commands

```bash
uv sync                                                        # creates .venv, installs package + dev group
uv run pytest                                                  # full suite (tests/)
uv run pytest tests/test_logger.py::test_protect_method_bare   # single test
uv run example.py                                              # usage demo; README points here
uv run ruff check --fix . && uv run ruff format .              # fix lint and formatting in place, then re-stage
uv run --python 3.13 pytest                                    # check the 3.13 floor (recreates .venv; `uv sync --python 3.14` to go back)
```

The project is managed with uv and builds with the `uv_build` backend (flat layout, so `module-root = ""`). Dev tools go in `[dependency-groups]` (`uv add --dev ...`), not optional extras. `uv.lock` is committed; re-run `uv lock` after editing dependencies.

Ruff is configured in `pyproject.toml` with a deliberately small rule set; `%`-formatting is allowed. `example.py` is deliberately minimal: four numbered steps (create, log, `exception()` with an error handler, `protect_method`) that show what the library is for. Keep it that short; the README's API section is where the full feature list lives. It doubles as a smoke test and makes no network calls.

When the public API changes, update all three: `example.py`, the README (usage snippet, the API section, and the migration notes if the change breaks callers), and this file.

## Committing

- Never commit without the user's explicit approval, given for that commit.
- Before asking for approval, stage the changes and run `/code-review` on the staged diff. Fix or report what it finds, then show the summary and a suggested commit message.
- `.claude/settings.json` registers a PreToolUse hook (`.claude/hooks/pre-commit-checks.sh`) that runs `ruff check`, `ruff format --check` and `pytest` on the staged snapshot when Claude runs `git commit`, and blocks the commit if any fail. Because it checks the index, stage everything first; don't use `git commit -a` or `git commit <paths>`. Fix the cause; don't bypass the hook. It doesn't run for commits made outside Claude Code.

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
