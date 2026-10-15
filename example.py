"""What python_logger does, in four steps. Run with: python example.py"""
from python_logger import Logger


# An error handler is your hook for alerts (email, Slack, ...). It runs whenever an exception is logged.
def alert(traceback, exc_info):
    print(">> ALERT:", traceback.format_exception_only(exc_info[0], exc_info[1])[-1].strip())


# 1. Create a logger. It prints to stdout; messages below log_level are hidden.
LOGGER = Logger(name="my_app", log_level="info", error_handler=alert)

# 2. Log messages.
LOGGER.debug("Hidden, because the level is info")
LOGGER.info("App started")
LOGGER.warning("Disk space is low")

# 3. Log a caught exception: prints the stacktrace, then calls the error handler.
try:
    1 / 0
except ZeroDivisionError as e:
    LOGGER.exception(e)


# 4. Protect a function: any exception is logged and handled as in step 3,
#    and the function returns exception_response instead of crashing.
@LOGGER.protect_method(exception_response=0)
def divide(a, b):
    return a / b


LOGGER.info("divide(10, 2) = %s" % divide(10, 2))
LOGGER.info("divide(1, 0) = %s" % divide(1, 0))   # Logged and alerted, returns 0
