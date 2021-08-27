from argparse import ArgumentParser
from pathlib import Path

if __name__ == '__main__':
    quit()

cliArgParser = ArgumentParser(
    description="A simple script for downloading files from Sci-Hub",
    epilog="This script works by parsing the response "
           "sent back from the server. "
           "Since different Sci-Hub mirrors may have different interfaces, "
           "and their layouts may change in the future, "
           "there is NO GUARANTEE that this script works on every mirror, "
           "or will continue to work on currently working mirrors "
           "in the future. "
)
cliArgParser.add_argument("--version", "-V",
                          action='version',
                          version="%(prog)s v0.7.1")
cliArgParser.add_argument("identifier",
                          type=str,
                          help="The identifier of the document. "
                               "If the string contains spaces, "
                               "it must be quoted. "
                               "Strings that are not recognized "
                               "will be taken as stripped DOI")
cliArgParser.add_argument("--proxy", "-p",
                          type=str,
                          help="Requests-type proxy argument. "
                               "Used for both HTTP and HTTPS. "
                               "Use socks5h://127.0.0.1:9150 "
                               "for TOR browser socks5 proxy. "
                               "Default: "
                               "no proxy"
                          )
cliArgParser.add_argument("--mirror", '-m',
                          type=str,
                          action='append',
                          help="Domain of file mirror to use. "
                               "Can specify multiple times to try "
                               "different mirrors. "
                               "Default: "
                               "https://sci-hub.se/")
cliArgParser.add_argument("--output", "-o",
                          type=str,
                          help="Save file with this name stem. "
                               "File extension part will always "
                               "follow from mirror. "
                               "Default: "
                               "the remote file name")
cliArgParser.add_argument("--dir", "-d",
                          type=str,
                          help="Download to this directory. "
                               "Relative path to current working directory. "
                               "Use ~ for home directory. "
                               "Default: "
                               "current working directory")
cliArgParser.add_argument("--chunk",
                          type=int,
                          default=8192,
                          help="Size of each download chunk, in bytes. "
                               "Default: "
                               "8192")
cliArgParser.add_argument("--useragent",
                          type=str,
                          default="Mozilla/5.0 "
                                  "(Windows NT 10.0; Win64; x64; rv:78.0) "
                                  "Gecko/20100101 Firefox/78.0",
                          help="The user agent string used. "
                               "If this script fails to get results "
                               "but you can find the requested papers "
                               "on the website, "
                               "try changing this. "
                               "Default: "
                               "Mozilla/5.0 (Windows NT 10.0; Win64; x64; "
                               "rv:78.0) Gecko/20100101 Firefox/78.0")
cliArgParser.add_argument("--autoname",
                          action='store_true',
                          help="Automatically name the file by its DOI "
                               "metadata. "
                               "May not give the best file name. "
                               "To specify its format, use --autoformat. "
                               "Has lower priority than --output")
cliArgParser.add_argument('--autoformat',
                          type=str,
                          default="[{authors}, {repo} {identifier}]{title}",
                          help="The format used for --autoname. "
                               "In Python str.format syntax. "
                               "Format containing space must be quoted. "
                               "Available keywords: "
                               "authors, authorEtAl, authorFamily, "
                               "authorFamilyCamel, identifier, repo, title, "
                               "title_, year, year2. "
                               "For details, refer to the repo README. "
                               "Default: "
                               "\"[{authors}, {repo} {identifier}]{title}\"")
cliArgParser.add_argument("--nocolor",
                          action='store_true',
                          help="Suppress color display")
cliArgParser.add_argument("--piping",
                          action='store_true',
                          help="Suppress all information, "
                               "Print only the absolute file path as "
                               "unquoted string if succeeds, "
                               "print nothing otherwise. "
                               "All errors are silently passed. "
                               "Implies --nocolor and no --verbose")
cliArgParser.add_argument("--dryrun",
                          action='store_true',
                          help="Do not actually write on disk or "
                               "download the file")
cliArgParser.add_argument("--config",
                          type=str,
                          default='~/.shdlconfig',
                          help="The path to the config file. "
                               "If the file exists and readable, "
                               "the following configs will be overridden "
                               "from file (instead of the CLI argument) "
                               "if they are present: "
                               "proxy, mirror, dir, chunk, useragent, "
                               "autoname, autoformat. "
                               "Pass an empty string to disable this. "
                               "Default: "
                               "~/.shdlconfig")
cliArgParser.add_argument("--verbose", "-v",
                          action='count',
                          default=0,
                          help="Display verbose information")
cliArg = vars(cliArgParser.parse_args())

# cliArg handling
import requests as rq
from urllib.parse import urlparse, urlunparse, unquote
from src.CommonUtil import *

cliArg['identifier'] = unquote(cliArg['identifier'])

# read config file if present
# if cliArg['config'] is None \
#         and (defPath := Path.home() / '.shdlconfig').is_file():
#     # get default
#     verbose_print("Default config file found")
#     cliArg['config'] = str(defPath)
# if cliArg['config'] is not None:
if cliArg['config'] != '':
    try:
        configPath = Path(cliArg['config']).expanduser()
        verbose_print("Looking for config file "
                      f"{PColor.PATH(str(configPath))}")
        if not configPath.is_file():
            raise FileNotFoundError
        configFileHandle = configPath.open('rt')
        verbose_print("Config file opened", 2)
        configDict = dict()
        verbose_print("Reading config file "
                      + PColor.PATH(str(configPath.resolve())))
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
                configDict['chunk'] = int(lineContent)
            elif lineHeader == 'autoname':
                configDict['autoname'] = lineContent = True
            else:
                isValidHeader = False
            if isValidHeader:
                verbose_print(f"Config {lineHeader} found "
                              f"with key {lineContent}")
        verbose_print(f"Overriding {list(configDict.keys())}", 2)
        cliArg.update(configDict)
    except FileNotFoundError:
        if cliArg['config'] == '~/.shdlconfig':  # is default
            verbose_print(f"{PColor.PATH('~/.shdlconfig')} not found")
        else:
            info_print("Config file not found "
                       f"at {PColor.PATH(cliArg['config'])}.")
    except PermissionError:
        info_print(PColor.ERROR("ERROR:"), end=" ")
        info_print("Cannot read specified config file "
                   f"{PColor.PATH(cliArg['config'])}")
    except ValueError:
        info_print(PColor.ERROR("ERROR:"), end=" ")
        info_print("Cannot parse config file. "
                   "Will revert to CLI arguments")
else:
    verbose_print("No config file", 2)

# check if dir is valid
if cliArg['dir'] is None:
    cliArg['dir'] = '.'
assert isinstance(cliArg['dir'], str)
cliArg['dir'] = cliArg['dir'].strip(" '\"")
try:
    cliArg['dir'] = (Path.cwd() / Path(cliArg['dir']).expanduser()).resolve(
        True)
    if not cliArg['dir'].is_dir():
        raise NotADirectoryError
except (NotADirectoryError, FileNotFoundError):
    error_reporter.quit_now(ErrorType.ARG_INVALID,
                            error_msg=f"{str(cliArg['dir'])} is not "
                                      "a valid directory")

# check mirror format
if cliArg['mirror'] is None:
    # info_print(PColor.ERROR("Error:"), end=" ")
    # info_print("No mirror provided")
    # error_reporter.quit_now(ErrorType.ARG_INVALID)
    cliArg['mirror'] = ("https://sci-hub.se/",)
else:
    cliArg['mirror'] = tuple(
        # enforce https if not specified
        urlunparse(urlparse(mirrorURL, scheme="https"))
        for mirrorURL in cliArg['mirror']
    )

# check network and proxy
cliArg['proxy'] = {scheme: cliArg['proxy'] for scheme in ('http', 'https')} \
    if cliArg['proxy'] is not None and cliArg['proxy'] != '' \
    else None
if cliArg['proxy'] is None:
    info_print(PColor.WARNING("WARNING:"), end=" ")
    info_print("No proxy configured")

verbose_print("Testing network connectivity ...")
try:
    pass
    rq.get('https://example.com',
           proxies=cliArg['proxy'],
           headers={'User-Agent': cliArg['useragent']})
except rq.exceptions.ProxyError:
    info_print(PColor.ERROR('ERROR:') + " Proxy config is invalid")
    error_reporter.quit_now(ErrorType.ARG_INVALID)
except rq.ConnectionError:
    info_print(PColor.ERROR("ERROR:") + " Failed to connect to the internet")
    if cliArg['proxy'] is not None:
        info_print("Maybe proxy is not setup correctly?")
    error_reporter.quit_now(ErrorType.NETWORK_ERROR)
except Exception as e:
    info_print(PColor.ERROR("ERROR:")
               + " Unknown error occurred when testing network connectivity")
    info_print(str(e))
    error_reporter.quit_now(ErrorType.NETWORK_ERROR)
else:
    if cliArg['proxy'] is not None:
        verbose_print(f"Using proxy {cliArg['proxy']['https']}")
cliArg['rqKwargs'] = {
    'proxies': cliArg['proxy'],
    'headers': {'User-Agent': cliArg['useragent'], }
}
