import argparse
from pathlib import Path

# ONLY IMPORT THIS TO READ CLI ARGUMENTS
# To get (processed) CLI arguments, import CommonUtil

_parser = argparse.ArgumentParser(
    description="A simple script for downloading files by their identifiers",
    epilog="This script works by parsing the response "
           "sent back from the server. "
           "Since different mirrors may have different response format, "
           "this script may not be able to parse the responses, and so "
           "there is no GUARANTEE that this script is suitable for your use. "
           "Use at your own risk. "
)
_parser.add_argument(
    "--version", "-V",
    action='version',
    version="%(prog)s v0.7.3"
)
_parser.add_argument(
    "identifier",
    type=str,
    help="The identifier of the document. "
         "If the string contains spaces, "
         "it must be quoted. "
         "Strings that are not recognized "
         "will be taken as stripped DOI"
)
_parser.add_argument(
    "--proxy", "-p",
    type=str,
    help="Requests-type proxy argument. "
         "Used for both HTTP and HTTPS. "
         "Use socks5h://127.0.0.1:9150 "
         "for TOR browser socks5 proxy. "
         "Default: "
         "no proxy"
)
_parser.add_argument(
    "--mirror", '-m',
    type=str,
    action='append',
    help="Domain of file mirror to use. "
         "Can specify multiple times to try "
         "different mirrors. "
)
_parser.add_argument(
    "--output", "-o",
    type=str,
    help="Save file with this name stem. "
         "File extension part will always "
         "follow from mirror. "
         "Default: "
         "the remote file name"
)
_parser.add_argument(
    "--dir", "-d",
    type=str,
    help="Download to this directory. "
         "Relative path to current working directory. "
         "Use ~ for home directory. "
         "Default: "
         "current working directory"
)
_parser.add_argument(
    "--chunk",
    type=int,
    help="Size of each download chunk, in bytes. "
         "Default: "
         "8192"
)
_parser.add_argument(
    "--useragent",
    type=str,
    help="The user agent string used. "
         "If this script fails to get results "
         "but you can find the requested papers "
         "on the website, "
         "try changing this. "
         "Default: "
         "Mozilla/5.0 (Windows NT 10.0; Win64; x64; "
         "rv:78.0) Gecko/20100101 Firefox/78.0"
)
_parser.add_argument(
    "--autoname",
    action='store_true',
    help="Automatically name the file by its DOI "
         "metadata. "
         "May not give the best file name. "
         "To specify its format, use --autoformat. "
         "Has lower priority than --output"
)
_parser.add_argument(
    '--autoformat',
    type=str,
    help="The format used for --autoname. "
         "In Python str.format syntax. "
         "Format containing space must be quoted. "
         "Available keywords: "
         "authors, authorEtAl, authorFamily, authors80, "
         "authorFamilyCamel, identifier, repo, title, "
         "title_, year, year2. "
         "For details, refer to the repo README. "
         "Default: "
         "\"[{authors}, {repo} {identifier}]{title}\""
)
_parser.add_argument(
    "--nocolor",
    action='store_true',
    help="Suppress color display"
)
_parser.add_argument(
    "--piping",
    action='store_true',
    help="Suppress all information, "
         "Print only the absolute file path as "
         "unquoted string if succeeds, "
         "print nothing otherwise. "
         "All errors are silently passed. "
         "Implies --nocolor and no --verbose"
)
_parser.add_argument(
    "--dryrun",
    action='store_true',
    help="Do not actually write on disk or "
         "download the file"
)
_parser.add_argument(
    "--config",
    type=str,
    default='~/.shdlconfig',
    help="The path to the config file. "
         "If the file exists and readable, "
         "the following configs will be overridden "
         "from file (instead of the CLI argument) "
         "if they are present: "
         "proxy, mirror, dir, chunk, useragent, "
         "autoname, autoformat, nocolor. "
         "Pass an empty string to disable this. "
         "Default: "
         "~/.shdlconfig"
)
_parser.add_argument(
    "--type",
    type=str,
    help="The query type of the input indentifier. "
         "Normally this is detected automatically. "
         "You can override the detection by specifying the type here. "
         "If this is used, the input identifier is assumed to contain "
         "only the identifier part (e.g. 10.XXXX/XXXXXX for DOI). "
         "Accepted value: doi, arxiv, ieee, jstor, pmid, sciencedirect"
)
_parser.add_argument(
    "--verbose", "-v",
    action='count',
    default=0,
    help="Display verbose information"
)
cliArg = vars(_parser.parse_args())
