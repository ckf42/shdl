from enum import Enum, IntEnum, unique

from CLIArgParser import cliArg


# print colors for xterm-256color
class PColor(Enum):
    DOI = '\033[94m'
    PATH = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    NULL = '\033[0m'

    def __call__(self, msg, color_display=cliArg.nocolor):
        if not color_display:
            return msg
        else:
            return f"{self.value}{msg}\033[0m"


def info_print(msg, *args, print_suppress=cliArg.piping, **kwargs):
    if not print_suppress:
        print(msg, *args, **kwargs)


def verbose_print(
        msg,
        msg_verbose_level=1,
        config_verbose_level=cliArg.verbose
        ):
    if msg_verbose_level <= config_verbose_level:
        info_print(msg)


def human_byte_unit_string(size_byte):
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

    def description(self):
        return {
                0: "Succeed",
                1: "Cannot write output",
                2: "Argument invalid",
                3: "Network connection error",
                4: "Query invalid",
                5: "Cannot fetch file"
                }.get(self.value, "UNKNOWN ERROR")


class ErrorReporterClass:
    _error_list = list()

    def __init__(self):
        self._error_list = list()

    def add_new_error(self, error_code):
        self._error_list.append(error_code)

    def quit_now(self, with_this_code=None):
        if with_this_code is not None:
            self._error_list = list(with_this_code)
        if ErrorType.SUCCEED in self._error_list:
            quit(0)
        else:
            return_error_code = self._error_list[0]
            info_print(PColor.ERROR("ERROR:")
                       + return_error_code.description())
            quit(return_error_code)


error_reporter = ErrorReporterClass()