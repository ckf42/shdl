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


@unique
class VerboseLevel(IntEnum):
    PRINT = 0
    INFO = 1
    VERBOSE = 2
    DEBUG = 3
    DETAIL = 4

    def _missing_(value, **kwargs):
        if value < (minVal := min(VerboseLevel.__members__.values())):
            return VerboseLevel(minVal)
        else:
            return VerboseLevel(max(VerboseLevel.__members__.values()))


def _base_print(msg: str,
                *args,
                print_suppress: bool = cliArg['piping'],
                **kwargs) -> None:
    # lower level print function
    if not print_suppress:
        print(msg, *args, **kwargs)


def console_print(
        msg: str,
        *args,
        msg_verbose_level: VerboseLevel = VerboseLevel.INFO,
        config_verbose_level: VerboseLevel = VerboseLevel(cliArg['verbose']),
        **kwargs) -> None:
    if msg_verbose_level <= config_verbose_level:
        _base_print(msg, *args, **kwargs)


def info_print(msg: str, *args, **kwargs):
    console_print(msg, msg_verbose_level=VerboseLevel.INFO, *args, **kwargs)


def human_byte_unit_string(size_byte: int) -> str:
    # assuming less than 1 GB
    if (val := size_byte / 1024 ** 2) >= 1:
        return f"{val :.2f} MB"
    elif (val := size_byte / 1024) >= 1:
        return f"{val :.2f} KB"
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


def quit_with_error(with_this_code: ErrorType = ErrorType.SUCCEED,
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
