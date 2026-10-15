"""Usage examples for python_logger. Run with: python example.py"""
import logging

from python_logger import Logger


def my_err_handler(traceback, exec_info):
    """A custom function to handle the errors
    This function receives two arguments, i.e. the traceback module and system exec info
    """
    print("Custom function invoked")
    print("Formatted exception")
    print(traceback.format_exc())
    print("System exec info")
    print(exec_info)
    exp_type, exp_value, exp_traceback = exec_info
    print("String formatted exception")
    print(traceback.format_exception(exp_type, exp_value, exp_traceback))
    print("End of custom function")


# 1. Basic logging
LOGGER = Logger(name="example_app", log_level="debug")
LOGGER.info("This is an info statement.")
LOGGER.debug("This is a debug statement with a value: %s" % str(123.456))

# 2. Log levels accept names or stdlib ints; messages below the level are dropped
LOGGER = Logger(name="warning_app", log_level=logging.WARNING)
LOGGER.info("This info statement is not printed")
LOGGER.warning("This warning statement is printed")

# 3. Context manager and exception logging (stacktrace only, no handler set)
with Logger(name="second_example_app") as LOGGER:
    try:
        LOGGER.info("This is also an info statement")
        LOGGER.debug(123456)
        a = 0 / 0                                   # Will print the divide by zero error message
    except Exception as e:
        LOGGER.error("Encountered error second_example_app")
        LOGGER.exception(e)

# 4. Custom error handler set after construction
with Logger(name="CUSTOM_ERROR_HANDLER") as LOGGER:
    LOGGER.info("Custom error handling example")
    LOGGER.debug("Will execute a function given by you in case of exception")
    if not LOGGER.set_custom_error_handler(my_err_handler):
        LOGGER.error("Unable to set custom error handler")
        raise SystemExit(1)
    try:
        LOGGER.debug("Divide by zero error")
        a = 0 / 0  # Will print the divide by zero error message
    except Exception as e:
        LOGGER.error("Encountered error CUSTOM_ERROR_HANDLER")
        LOGGER.exception(e)

# 5. Custom error handler passed at construction, with protected methods
LOGGER = Logger(name="PROTECTED_METHODS", log_level="info", error_handler=my_err_handler)


@LOGGER.protect_method
def divide(a, b):
    return a / b


@LOGGER.protect_method(exception_response="fallback")
def add(a, b):
    return a + b


LOGGER.info("divide(4, 2) returned: %s" % divide(4, 2))
LOGGER.info("divide(1, 0) returned: %s" % divide(1, 0))      # Handler runs, returns None
LOGGER.info("add('2', 2) returned: %s" % add("2", 2))        # Handler runs, returns "fallback"
