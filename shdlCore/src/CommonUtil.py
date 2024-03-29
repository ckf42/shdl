from enum import Enum, IntEnum, unique
from typing import Optional, NoReturn
from pathlib import Path
from urllib.parse import urlparse, urlunparse, unquote

import requests as rq

from .CliArg import cliArg


# functions defined before cliArg postprocessing use only verbose, piping

@unique
class VerboseLevel(IntEnum):
    PRINT = 0  # always print unless explicitly suppressed
    INFO = 1
    VERBOSE = 2
    DEBUG = 3
    DETAIL = 4

    def _missing_(value, **kwargs):
        if value < (minVal := min(VerboseLevel.__members__.values())):
            return VerboseLevel(minVal)
        else:
            return VerboseLevel(max(VerboseLevel.__members__.values()))


def console_print(
        msg: str,
        *args,
        msg_verbose_level: VerboseLevel = VerboseLevel.PRINT,
        print_suppress: bool = cliArg['piping'],
        **kwargs) -> None:
    if not print_suppress \
            and msg_verbose_level <= cliArg['verbose']:
        print(msg, *args, **kwargs)


def info_print(msg: str, *args, **kwargs):
    # sugar
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


console_print("Raw cli arguments: ",
              msg_verbose_level=VerboseLevel.DEBUG)
for _k, _v in cliArg.items():
    console_print(f"{_k}: {str(_v)}",
                  msg_verbose_level=VerboseLevel.DEBUG)

# do cliArg postprocess

_defaultDict = {
    # default arguments for arg that may be overridden in shdlconfig
    'useragent':  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) '
                  'Gecko/20100101 Firefox/78.0',
    'autoformat': '[{authors}, {repo} {identifier}]{title}',
    'dir':        '.',
    'proxy':      '',
    'chunk':      8192,
}
# check if has config file
if cliArg['config'] != '':
    configFileHandle = None
    configDict = dict()
    try:
        # cannot use color print
        configPath = Path(cliArg['config']).expanduser().resolve(strict=True)
        console_print(f"Looking for config file {configPath}",
                      msg_verbose_level=VerboseLevel.DEBUG)
        if not configPath.is_file():
            raise FileNotFoundError
        configFileHandle = configPath.open('rt')
        console_print("Config file opened",
                      msg_verbose_level=VerboseLevel.DEBUG)
        console_print(f"Reading config file {configPath}",
                      msg_verbose_level=VerboseLevel.DEBUG)
        for configLine in configFileHandle:
            if '=' not in configLine:
                continue
            splittedLine = configLine.strip().split('=', 1)
            lineHeader = splittedLine[0].lower()
            lineContent = '' if len(splittedLine) <= 1 else splittedLine[1]
            isValidHeader = True
            if lineHeader in ('proxy', 'dir', 'useragent', 'autoformat'):
                configDict[lineHeader] = lineContent
            elif lineHeader == 'mirror':
                if 'mirror' not in configDict:
                    configDict['mirror'] = list((lineContent,))
                else:
                    configDict['mirror'].append(lineContent)
            elif lineHeader == 'chunk':
                # raise ValueError if casting fails
                configDict['chunk'] = int(lineContent)
            elif lineHeader in ('autoname', 'nocolor'):
                configDict[lineHeader] = lineContent = True
            else:
                isValidHeader = False
            if isValidHeader:
                console_print(f"Config {lineHeader} found "
                              f"with key {lineContent}",
                              msg_verbose_level=VerboseLevel.DEBUG)
        configFileHandle.close()
        console_print(f"Config file specified {list(configDict.keys())}",
                      msg_verbose_level=VerboseLevel.DEBUG)
    except (FileNotFoundError, IsADirectoryError):
        if cliArg['config'] == '~/.shdlconfig':  # is default
            info_print("'~/.shdlconfig' not found")
        else:
            info_print("Config file not found "
                       f"at {cliArg['config']}.")
    except PermissionError:
        info_print("ERROR:", end=" ")
        info_print("Cannot read specified config file "
                   f"{cliArg['config']}")
    except (ValueError, RuntimeError):
        # force close configFileHandle if possible
        getattr(configFileHandle, 'close', lambda: None)()
        info_print("ERROR:", end=" ")
        info_print("Cannot parse config file. "
                   "Will revert to CLI arguments")
    else:
        # config file read to configDict
        _defaultDict.update(configDict)
else:
    console_print("No config file",
                  msg_verbose_level=VerboseLevel.VERBOSE)

# assign default parameter (may be overriden in config file)
for _k, _v in _defaultDict.items():
    if cliArg[_k] is None or cliArg[_k] is False:
        cliArg[_k] = _v


# default is applied, can define these two
# print colors for xterm-256color
class PColor(Enum):
    ID = '\033[94m'
    PATH = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    INFO = '\033[96m'
    NULL = '\033[0m'

    def __call__(self,
                 msg: str,
                 color_display: bool = not cliArg['nocolor']) -> str:
        if not color_display:
            return msg
        else:
            return f"{self.value}{msg}\033[0m"


def quit_with_error(with_this_code: ErrorType = ErrorType.SUCCEED,
                    error_msg: Optional[str] = None) -> NoReturn:
    import sys
    if with_this_code == ErrorType.SUCCEED:
        sys.exit(0)
    else:
        console_print(PColor.ERROR.__call__("ERROR:")
                      + " "
                      + (with_this_code.description()
                         if error_msg is None
                         else error_msg))
        sys.exit(int(with_this_code))


# start checking parameters validity
console_print("Start checking cli arguments",
              msg_verbose_level=VerboseLevel.DEBUG)
cliArg['identifier'] = unquote(cliArg['identifier'])
assert isinstance(cliArg['dir'], str)
try:
    cliArg['dir'] = (
            Path.cwd() / Path(cliArg['dir'].strip(" '\"")).expanduser()
    ).resolve(strict=True)
    if not cliArg['dir'].is_dir():
        raise NotADirectoryError
except (NotADirectoryError, FileNotFoundError):
    quit_with_error(ErrorType.ARG_INVALID,
                    error_msg=f"{str(cliArg['dir'])} is not a valid directory")

if cliArg['mirror'] is None:
    # should not quit without mirror: arxiv never needs one
    # quit_with_error(ErrorType.ARG_INVALID,
    #                 error_msg="No mirror provided. "
    #                           "Please specify at least a mirror "
    #                           "in commandline argument "
    #                           "or in shdlconfig file")
    cliArg['mirror'] = tuple()
else:
    cliArg['mirror'] = tuple(
        # enforce https unless specified, dirty hack
        urlunparse(
            urlparse(('//' if '//' not in mirrorURL else '') + mirrorURL,
                     scheme="https")
        )
        for mirrorURL in cliArg['mirror']
    )

if cliArg['proxy'] == '':
    cliArg['proxy'] = None
if cliArg['proxy'] is not None:
    cliArg['proxy'] = {
            'nop': None,
            'tor': 'socks5h://127.0.0.1:9050',
            'tbb': 'socks5h://127.0.0.1:9150',
        }.get(cliArg['proxy'].lower(), cliArg['proxy'])
    cliArg['proxy'] = { scheme: cliArg['proxy'] for scheme in ('http', 'https') } \
        if cliArg['proxy'] is not None \
        else None
if cliArg['proxy'] is None:
    console_print(PColor.WARNING.__call__("WARNING:"), end=" ",
                  msg_verbose_level=VerboseLevel.INFO)
    console_print("No proxy configured",
                  msg_verbose_level=VerboseLevel.INFO)

# network para
cliArg['rqKwargs'] = {
    'proxies': cliArg['proxy'],
    'headers': {'User-Agent': cliArg['useragent'], }
}
info_print("Testing network connectivity ...")
try:
    rq.get('https://example.com/', **cliArg['rqKwargs'])
except rq.exceptions.ProxyError:
    quit_with_error(ErrorType.ARG_INVALID,
                    error_msg="Proxy config is invalid")
except rq.ConnectionError:
    quit_with_error(ErrorType.NETWORK_ERROR,
                    error_msg="Failed to connect to the internet. "
                              + ("Maybe proxy is not setup correctly?"
                                 if cliArg['proxy'] is not None
                                 else ""))
except Exception as e:
    quit_with_error(ErrorType.NETWORK_ERROR,
                    error_msg=("Unknown error occurred "
                               "when testing network connectivity. \n"
                               + str(e)))
else:
    if cliArg['proxy'] is not None:
        info_print(f"Using proxy {cliArg['proxy']['https']}")

if cliArg['type'] is not None:
    cliArg['type'] = cliArg['type'].lower()
    from .RepoHandler.RegisteredRepo import registered_repo_name

    if cliArg['type'] not in registered_repo_name:
        quit_with_error(ErrorType.ARG_INVALID,
                        error_msg=f"Input type {cliArg['type']} does not "
                                  "match any known repo name")

console_print("Processed cli arguments: ",
              msg_verbose_level=VerboseLevel.DEBUG)
for _k, _v in cliArg.items():
    console_print(PColor.INFO.__call__(_k) + ": " + str(_v),
                  msg_verbose_level=VerboseLevel.DEBUG)
