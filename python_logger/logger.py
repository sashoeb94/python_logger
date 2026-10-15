"""Generic class for Python logging and exception handling"""
from functools import wraps
import logging
import sys
import traceback

DEFAULT_FORMAT = "%(asctime)s : %(name)s : %(levelname)s : %(message)s"
DEFAULT_LOG_LEVEL = "debug"
LOG_LEVELS = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
    "unset": logging.NOTSET,
}


class Logger:
    """Python Logger class"""

    def __init__(self, name, log_level=DEFAULT_LOG_LEVEL, log_format=DEFAULT_FORMAT, error_handler=None):
        """Initializes the logger"""
        if error_handler is not None and not callable(error_handler):
            raise TypeError("error_handler must be callable, got %r" % (error_handler,))
        self._error_handler = None
        self._logger = self._build_logger(name, self._get_log_level(log_level), log_format)
        self.debug = self._logger.debug
        self.info = self._logger.info
        self.warning = self._logger.warning
        self.error = self._logger.error
        self.critical = self._logger.critical
        if error_handler is not None:
            self.set_custom_error_handler(error_handler)

    def __enter__(self):
        """Use with for invocation"""
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Use with for invocation"""
        return None

    @staticmethod
    def _get_log_level(log_level):
        if isinstance(log_level, int) and not isinstance(log_level, bool):
            return log_level
        if isinstance(log_level, str) and log_level.lower() in LOG_LEVELS:
            return LOG_LEVELS[log_level.lower()]
        raise ValueError("Unknown log level %r, expected an int or one of %s" % (log_level, ", ".join(LOG_LEVELS)))

    @staticmethod
    def _build_logger(name, log_level, log_format):
        """Builds a private (unregistered) logger writing to stdout.
        Only the logger has a level, so LOGGER.setLevel() later also changes what reaches stdout.
        """
        logger = logging.Logger(name, log_level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(handler)
        return logger

    @property
    def LOGGER(self):
        """Returns the underlying logging.Logger object"""
        return self._logger

    def protect_method(self, method=None, exception_response=None):
        """Returns a wrapper function which adds a try/except block around the supplied method.
        If an exception is raised in the method, it is passed to exception() and exception_response is returned.
        Usable as @LOGGER.protect_method or @LOGGER.protect_method(exception_response=...).
        """
        def override_exception_return(protected_method):
            @wraps(protected_method)
            def wrapper(*args, **kwargs):
                try:
                    return protected_method(*args, **kwargs)
                except Exception as e:
                    self.exception(e)
                    return exception_response
            return wrapper
        if method is None:
            return override_exception_return
        if not callable(method):
            raise TypeError("protect_method takes the function to wrap; pass exception_response by keyword")
        return override_exception_return(method)

    def exception(self, message):
        """Logs the exception message with stacktrace and runs the custom error handler if set.
        Call it from inside an except block.
        """
        self._logger.exception(message)
        exc_info = sys.exc_info()
        if self._error_handler is None or exc_info[0] is None:
            return
        func_name = getattr(self._error_handler, "__name__", repr(self._error_handler))
        self._logger.debug("Executing custom error handler %s" % func_name)
        try:
            self._error_handler(traceback, exc_info)
        except Exception:
            self._logger.exception("Custom error handler %s failed" % func_name)
        else:
            self._logger.debug("Executed custom error handler")

    def set_custom_error_handler(self, func):
        """Sets a custom handler to be executed during exception.
        The function should accept two arguments: the traceback module and sys.exc_info().
        Returns True if able to set else False.
        """
        self._logger.debug("Setting custom error handler")
        if not callable(func):
            self._logger.error("NEED A FUNCTION AS AN ARGUMENT")
            self._logger.error("CUSTOM ERROR HANDLER NOT SET")
            return False
        self._error_handler = func
        self._logger.debug("Custom error handler set")
        return True
