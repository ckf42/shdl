from enum import Enum, IntEnum, unique
from typing import Optional, NoReturn

from src.CLIArgParser import *

if __name__ == '__main__':
    quit()


# print colors for xterm-256color
class PColor(Enum):
    DOI = '\033[94m'
    PATH = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    NULL = '\033[0m'

    def __call__(self, msg: str,
                 color_display: bool = not cliArg['nocolor']) -> str:
        if not color_display:
            return msg
        else:
            return f"{self.value}{msg}\033[0m"


def info_print(msg: str, *args, print_suppress: bool = cliArg['piping'],
               **kwargs) -> None:
    if not print_suppress:
        print(msg, *args, **kwargs)


def verbose_print(msg: str,
                  msg_verbose_level: int = 1,
                  config_verbose_level: int = cliArg['verbose']) -> None:
    if msg_verbose_level <= config_verbose_level:
        info_print(msg)


def human_byte_unit_string(size_byte: int) -> str:
    if size_byte >= 1024 ** 2:
        return f"{size_byte / (1024 ** 2) :.2f} MB"
    elif size_byte >= 1024:
        return f"{size_byte / 1024 :.2f} KB"
    else:
        return f"{size_byte} B"


@unique
class ErrorType(IntEnum):
    SUCCEED = 0
    OUTPUT_ERROR = 1
    ARG_INVALID = 2
    NETWORK_ERROR = 3
    QUERY_INVALID = 4
    FILE_NOT_FOUND = 5

    def description(self) -> str:
        return {
            0: "Succeed",
            1: "Cannot write to output",
            2: "Argument invalid",
            3: "Network connection error",
            4: "Query string is invalid",
            5: "Cannot fetch file from remote"
        }.get(self.value, "UNKNOWN ERROR")


def quit_with_error(with_this_code: Optional[ErrorType] = None,
                    error_msg: Optional[str] = None) -> NoReturn:
    if with_this_code == ErrorType.SUCCEED:
        quit(0)
    else:
        info_print(PColor.ERROR.__call__("ERROR:")
                   + " "
                   + (with_this_code.description()
                      if error_msg is None
                      else error_msg))
        quit(with_this_code)
