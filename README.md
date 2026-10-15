# Python Logger
Generic library for Python logging and exception handling. Requires Python 3.13+, no third-party dependencies.

# Install
The package isn't on PyPI. Add it to a uv project straight from GitHub:
```bash
uv add git+https://github.com/sashoeb94/python_logger
```
Or install it from a clone with `uv pip install -e .` (plain `pip install -e .` works too).

# Usage
```python
from python_logger import Logger

def on_error(traceback, exc_info):
    print(traceback.format_exception(*exc_info))

LOGGER = Logger(name="my_app", log_level="info", error_handler=on_error)

@LOGGER.protect_method(exception_response=None)
def risky():
    return 1 / 0

risky()  # logs the stacktrace, calls on_error, returns None
```

Find more example code in the example.py file (`uv run example.py`).

# API

## `Logger(name, log_level="debug", log_format=DEFAULT_FORMAT, error_handler=None)`
Creates a logger that writes to stdout. Each instance is independent: two loggers with the same name don't share handlers or settings.

- `log_level`: `"critical"`, `"error"`, `"warning"`, `"info"`, `"debug"` or `"unset"` (case-insensitive), or a stdlib level such as `logging.INFO`. Anything else (an unknown name, `None`, a bool) raises `ValueError`. To change the level later, call `LOGGER.LOGGER.setLevel(...)`.
- `log_format`: a `logging.Formatter` format string. The default is `"%(asctime)s : %(name)s : %(levelname)s : %(message)s"`.
- `error_handler`: optional callable run by `exception()`. Same as calling `set_custom_error_handler`, except that a non-callable raises `TypeError`.

Works as a context manager (`with Logger("app") as LOGGER:`). Exceptions raised inside the block aren't suppressed.

## Methods
| Method | Description |
| --- | --- |
| `debug` / `info` / `warning` / `error` / `critical` | Standard `logging` calls. |
| `exception(message)` | Logs `message` with the current stacktrace, then calls the error handler if one is set. Call it inside an `except` block; outside one, the handler isn't called. |
| `set_custom_error_handler(func)` | Sets the error handler. Returns `True` if set, or `False` if `func` isn't callable. |
| `protect_method` | Decorator that catches exceptions in the wrapped function, passes them to `exception()` and returns `exception_response` instead. Use it bare (`@LOGGER.protect_method`, returns `None`) or with an argument (`@LOGGER.protect_method(exception_response=-1)`). `exception_response` must be passed by keyword; a positional non-function raises `TypeError`. |
| `LOGGER` | Property returning the underlying `logging.Logger`, e.g. to add more handlers. |

## Error handlers
An error handler is called as `handler(traceback, exc_info)`:
- `traceback`: the stdlib `traceback` module
- `exc_info`: the `sys.exc_info()` tuple `(type, value, traceback)`

Use it to send alerts (email, Slack, Sentry, …) or anything else. If the handler raises, that error is logged and the original exception isn't masked.

# Development
The project is managed with [uv](https://docs.astral.sh/uv/).
```bash
uv sync         # creates .venv and installs the package plus the dev group (pytest, ruff)
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

# Migrating from the Python 2 version
- Import from the package: `from python_logger import Logger` (previously `from app_logger import Logger`).
- Built-in Mailgun email alerts and `email_config.py` were removed. Send alerts from an error handler instead.
- The `send_alerts`, `is_service` and `instance` constructor arguments were removed.
- An unknown `log_level` now raises `ValueError` instead of silently falling back to `NOTSET`.
- `protect_method` now needs `exception_response` as a keyword argument.
- Error handlers keep the same `(traceback, exc_info)` signature, so existing handlers work unchanged.
