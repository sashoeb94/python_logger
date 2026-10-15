import logging
import traceback

import pytest

from python_logger import Logger


def test_logs_to_stdout_with_default_format(capsys):
    Logger("app").info("hello")
    out = capsys.readouterr().out
    assert " : app : INFO : hello" in out


def test_level_filtering(capsys):
    logger = Logger("app", log_level="INFO")
    logger.debug("hidden")
    logger.info("shown")
    out = capsys.readouterr().out
    assert "hidden" not in out
    assert "shown" in out


def test_int_level(capsys):
    logger = Logger("app", log_level=logging.WARNING)
    logger.info("hidden")
    logger.warning("shown")
    out = capsys.readouterr().out
    assert "hidden" not in out
    assert "shown" in out


@pytest.mark.parametrize("level", ["verbose", None, True, 1.5])
def test_invalid_level_raises_value_error(level):
    with pytest.raises(ValueError):
        Logger("app", log_level=level)


def test_runtime_level_change_reaches_stdout(capsys):
    logger = Logger("app", log_level="info")
    logger.LOGGER.setLevel(logging.DEBUG)
    logger.debug("now visible")
    assert "now visible" in capsys.readouterr().out


def test_exception_calls_handler_inside_except(capsys):
    calls = []
    logger = Logger("app", error_handler=lambda tb, exc_info: calls.append((tb, exc_info)))
    try:
        1 / 0
    except ZeroDivisionError as e:
        logger.exception(e)
    assert len(calls) == 1
    tb, (exc_type, exc_value, exc_tb) = calls[0]
    assert tb is traceback
    assert exc_type is ZeroDivisionError
    assert "Traceback" in capsys.readouterr().out


def test_exception_outside_except_skips_handler():
    calls = []
    logger = Logger("app", error_handler=lambda *args: calls.append(args))
    logger.exception("no active exception")
    assert calls == []


def test_failing_handler_does_not_propagate(capsys):
    def bad_handler(tb, exc_info):
        raise RuntimeError("handler broke")

    logger = Logger("app", error_handler=bad_handler)
    try:
        1 / 0
    except ZeroDivisionError as e:
        logger.exception(e)
    assert "Custom error handler bad_handler failed" in capsys.readouterr().out


def test_set_custom_error_handler_rejects_non_callable():
    assert Logger("app").set_custom_error_handler("not a function") is False


def test_constructor_rejects_non_callable_error_handler():
    with pytest.raises(TypeError):
        Logger("app", error_handler="not a function")


def test_protect_method_bare():
    calls = []
    logger = Logger("app", error_handler=lambda *args: calls.append(args))

    @logger.protect_method
    def divide(a, b):
        return a / b

    assert divide(4, 2) == 2
    assert divide(1, 0) is None
    assert divide.__name__ == "divide"
    assert len(calls) == 1


def test_protect_method_with_response():
    logger = Logger("app")

    @logger.protect_method(exception_response=-1)
    def divide(a, b):
        return a / b

    assert divide(1, 0) == -1
    assert divide.__name__ == "divide"


@pytest.mark.parametrize("response", [0, -1, "fallback"])
def test_protect_method_rejects_positional_response(response):
    with pytest.raises(TypeError):
        Logger("app").protect_method(response)


def test_instances_are_independent(capsys):
    first = Logger("same", error_handler=lambda *args: None)
    second = Logger("same")
    second.info("once")
    assert capsys.readouterr().out.count("once") == 1
    assert second._error_handler is None
    assert first.LOGGER is not second.LOGGER


def test_context_manager_does_not_swallow():
    with pytest.raises(ZeroDivisionError):
        with Logger("app") as logger:
            assert isinstance(logger, Logger)
            1 / 0
