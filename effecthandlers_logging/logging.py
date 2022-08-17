import os
import sys
import warnings
from enum import Enum
from typing import Any, Callable, Optional, TextIO, TypeVar

import attr
from colors import color
from effecthandlers import Handler, Message, NoHandlerError, ReturnValue, send
from pendulum.datetime import DateTime


class LogLevel(Enum):
    DEBUG = 0
    INFO = 10
    WARNING = 50
    ERROR = 100


MessageType = TypeVar("MessageType")


@attr.define
class LogMessage(Message):
    message: Any
    level: LogLevel = LogLevel.INFO


def _format_text_message(text, level):
    if level == LogLevel.DEBUG:
        level_str = color("DEBUG", fg="#555555")
    elif level == LogLevel.INFO:
        level_str = "INFO"
    elif level == LogLevel.WARNING:
        level_str = color("WARNING", fg="#ffff00")
    elif level == LogLevel.ERROR:
        level_str = color("ERROR", fg="#ff0000", style="bold")
    else:
        raise NotImplementedError()
    return "\n".join(
        [
            "  ".join(
                [
                    "[ {} ]".format(DateTime.now().to_datetime_string()),
                    level_str,
                    color("({})".format(str(os.getpid())), fg="Gray"),
                    x,
                ]
            )
            for x in text.split("\n")
        ]
    )


def _default_log_message_formatter(log_message: LogMessage) -> str:
    match log_message:
        case LogMessage(str(text), level):
            return _format_text_message(text, level)
        case _:
            raise NotImplementedError()


class TextLogger(Handler):
    def __init__(
        self,
        sink: Optional[TextIO | list[TextIO]] = None,
        formatter: Optional[Callable[[LogMessage], str]] = None,
    ) -> None:
        if formatter is None:
            formatter = _default_log_message_formatter
        self._formatter = formatter

        if sink is None:
            sink = sys.stderr
        if not isinstance(sink, list):
            sink = [sink]
        self.sink = sink

    def handle(self, message: Message) -> Any:
        match message:
            case LogMessage():
                try:
                    formatted_message = self._formatter(message)
                except NotImplementedError:
                    return
                for sink in self.sink:
                    sink.write(formatted_message)
                    sink.write("\n")
                    sink.flush()
                try:
                    send(message, interpret_final=False)
                except NoHandlerError:
                    return ReturnValue(None)


def log(level: LogLevel, message: Any) -> None:
    try:
        send(
            LogMessage(
                message=message,
                level=level,
            )
        )
    except NoHandlerError:
        warnings.warn(f'No handler for log message of type "{type(message).__name__}"')


def log_debug(message: Any) -> None:
    return log(LogLevel.DEBUG, message)


def log_info(message: Any) -> None:
    return log(LogLevel.INFO, message)


def log_warning(message: Any) -> None:
    return log(LogLevel.WARNING, message)


def log_error(message: Any) -> None:
    return log(LogLevel.ERROR, message)
