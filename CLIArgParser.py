from argparse import ArgumentParser
from pathlib import Path

if __name__ == '__main__':
    quit()

cliArgParser = ArgumentParser(
    description="A simple script for downloading files from Sci-Hub",
    epilog="This script works by parsing the response sent back from the server. "
           "Since different Sci-Hub mirrors may have different interfaces, "
           "and their layouts may change in the future, "
           "there is NO GUARANTEE that this script works on every mirror, "
           "or will continue to work on currently working mirrors in the future. "
)
cliArgParser.add_argument("--version", "-V",
                          action='version',
                          version="% (prog)s v0.5.0")
cliArgParser.add_argument("doi",
                          type=str,
                          help="The DOI string of the document. "
                               "If the string contains spaces, "
                               "it must be quoted")
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
                               "Can specify multiple times to try different mirrors. "
                               "Default: "
                               "https://sci-hub.se/")
cliArgParser.add_argument("--output", "-o",
                          type=str,
                          help="Save file with this name stem. "
                               "File extension part will always follow from mirror. "
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
                               "but you can find the requested papers on the website, "
                               "try changing this. "
                               "Default: "
                               "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) "
                               "Gecko/20100101 Firefox/78.0")
cliArgParser.add_argument("--autoname",
                          action='store_true',
                          help="Automatically name the file by its DOI metadata. "
                               "May not give the best file name. "
                               "Format: [<authors>, doi <doi>]<title>. "
                               "Has lower priority than --output")
cliArgParser.add_argument("--nocolor",
                          action='store_true',
                          help="Suppress color display")
cliArgParser.add_argument("--piping",
                          action='store_true',
                          help="Suppress all information, "
                               "Print only the absolute file path as unquoted string "
                               "if succeeds, "
                               "print nothing otherwise. "
                               "All errors are silently passed. "
                               "Implies --nocolor and no --verbose")
cliArgParser.add_argument("--dryrun",
                          action='store_true',
                          help="Do not actually write on disk or download the file")
cliArgParser.add_argument("--verbose", "-v",
                          action='count',
                          default=0,
                          help="Display verbose information")
cliArg = cliArgParser.parse_args()

from CommonUtil import *

if cliArg.dir is None:
    cliArg.dir = '.'
try:
    cliArg.dir = (Path.cwd() / Path(cliArg.dir).expanduser()).resolve(True)
    if not cliArg.dir.is_dir():
        raise NotADirectoryError
except (NotADirectoryError, FileNotFoundError):
    info_print(PColor.ERROR("ERROR:"), end=" ")
    info_print(f"{str(cliArg.dir)} is not a valid directory")
    error_reporter.quit_now(ErrorType.ARG_INVALID)