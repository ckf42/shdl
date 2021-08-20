#!/usr/bin/env python3
# TODO use urllib.request instead?
import requests as rq
import re
from argparse import ArgumentParser as aAP
from urllib.parse import urljoin, urlunparse, urlparse
import pathlib
# for filename normalization
# TODO use unidecode instead?
from unicodedata import normalize as ucNormalize
# for arxiv metadata parsing
from xml.etree import ElementTree as eTree
# for type hint
from typing import BinaryIO, Union
from collections.abc import Callable


# parser setup
parser = aAP(description="A simple script for downloading files from Sci-Hub",
             epilog="This script works by parsing the response "
             "sent back from the server. "
             "Since different Sci-Hub mirrors may have different interfaces, "
             "and their layouts may change in the future, "
             "there is NO GUARANTEE that this script works on every mirror, "
             "or will continue to work on currently working mirrors "
             "in the future. ")
parser.add_argument("--version", "-V",
                    action='version',
                    version="% (prog)s v0.5.0")
parser.add_argument("doi",
                    type=str,
                    help="The DOI string of the document. "
                    "If the string contains spaces, it must be quoted")
parser.add_argument("--proxy", "-p",
                    type=str,
                    help="Requests-type proxy argument. "
                    "Used for both HTTP and HTTPS. "
                    "Use socks5h://127.0.0.1:9150 "
                    "for TOR browser socks5 proxy. "
                    "Default: "
                    "no proxy"
                    )
parser.add_argument("--mirror", '-m',
                    type=str,
                    action='append',
                    help="Domain of scihub mirror to use. "
                    "Can specify multiple times to try different mirrors. "
                    "Default: "
                    "https://sci-hub.se/")
parser.add_argument("--output", "-o",
                    type=str,
                    help="Save file with this name stem. "
                    "File extension part will always follow from mirror. "
                    "Default: "
                    "the remote file name")
parser.add_argument("--dir", "-d",
                    type=str,
                    help="Download to this directory. "
                    "Relative path to current working directory. "
                    "Use ~ for home directory. "
                    "Default: "
                    "current working directory")
parser.add_argument("--chunk",
                    type=int,
                    default=8192,
                    help="Size of each download chunk, in bytes. "
                    "Default: "
                    "8192")
parser.add_argument("--useragent",
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
parser.add_argument("--autoname",
                    action='store_true',
                    help="Automatically name the file by its DOI metadata. "
                    "May not give the best file name. "
                    "Format: [<authors>, doi <doi>]<title>. "
                    "Has lower priority than --output")
parser.add_argument("--nocolor",
                    action='store_true',
                    help="Suppress color display")
parser.add_argument("--verbose", "-v",
                    action='count',
                    default=0,
                    help="Display verbose information")
args = parser.parse_args()

# errorcode:
# 0: success
# 1: cannot write output file
# 2: argument error
# 3: cannot connect to internet
# 4: query string invalid
# 5: cannot fetch file


# print colors for xterm-256color
def pcolors(msg: str,
            msgType: str,
            colorDisplay: bool = not args.nocolor) -> str:
    if not colorDisplay:
        return msg
    frontColorSeq = {
        'DOI': '\033[94m',
        'PATH': '\033[92m',
        'WARNING': '\033[93m',
        'ERROR': '\033[91m',
        'BOLD': '\033[1m',
        'UNDERLINE': '\033[4m',
        # 'ENDC': '\033[0m',
    }.get(msgType.upper(), '\033[0m')
    return f"{frontColorSeq}{msg}\033[0m"


def humanByteUnitString(s: int) -> str:
    if s >= 1024 ** 2:
        return f"{s / (1024 ** 2) :.2f} MB"
    elif s >= 1024:
        return f"{s / 1024 :.2f} KB"
    else:
        return f"{s} B"


def verbosePrint(msg: str,
                 msgVerboseLevel: int = 1,
                 configVerboseLevel: int = args.verbose) -> None:
    if msgVerboseLevel <= configVerboseLevel:
        print(msg)


def transformToAuthorStr(authorList: tuple[tuple[str]]) -> str:
    # authorList assumed (given name, family name)
    return ', '.join(''.join((gNamePart
                              if len(gNamePart) <= 1 or not gNamePart.isalpha()
                              else (gNamePart[0] + '.'))
                             for gNamePart
                             in re.split(r'\b', authorNameTuple[0]))
                     + ' '
                     + authorNameTuple[1]
                     for authorNameTuple in authorList)


# list modified from https://gist.github.com/sebleier/554280
stopwordLst = (
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an',
    'and', 'any', 'are', 'as', 'at', 'be', 'because', 'been', 'before',
    'being', 'below', 'between', 'both', 'but', 'by', 'can', 'did', 'do',
    'does', 'doing', 'don', 'down', 'during', 'each', 'few', 'for', 'from',
    'further', 'had', 'has', 'have', 'having', 'here', 'how', 'if', 'in',
    'into', 'is', 'just', 'more', 'most', 'no', 'nor', 'not', 'now', 'of',
    'off', 'on', 'once', 'only', 'or', 'other', 'out', 'over', 'own', 's',
    'same', 'should', 'so', 'some', 'such', 't', 'than', 'that', 'the', 'then',
    'there', 'these', 'this', 'those', 'through', 'to', 'too', 'under',
    'until', 'up', 'very', 'was', 'were', 'what', 'when', 'where', 'which',
    'while', 'who', 'whom', 'why', 'will', 'with',
)


# TODO better method?
def transformToTitle(s: str) -> str:
    wordsInSent = re.split('\\b',
                           re.sub('</?mml.+?>', '', s.strip(' ,."\'')))
    if len(wordsInSent) <= 1:
        return s
    return wordsInSent[1] + ''.join(
        (w.lower() if w.lower() in stopwordLst else w.capitalize())
        for w in wordsInSent[2:]
    )


def sanitizeString(s: str) -> str:
    # TODO use unidecode.unidecode instead?
    return ucNormalize(
        'NFKD',
        s
        .translate(str.maketrans({k: '' for k in '/<>:\"\\|?*'}))
        .translate(str.maketrans({'’': '\''}))
    ).encode('ASCII', 'ignore').decode()


def checkMetaInfoResponseValidity(res: rq.Response, metaType: str) -> bool:
    if metaType == 'doi':
        return res.status_code == 200 \
            and res.headers['content-type'] == ('application/'
                                                'vnd.citationstyles.csl+json')
    elif metaType == 'arxiv':
        return res.status_code == 200 \
            and 'http://arxiv.org/api/errors' not in res.text
    else:
        raise ValueError(f"Unknown metaType {metaType}")


def getMetaInfoFromResponse(res: rq.Response,
                            metaType: str) -> tuple[tuple[str], str]:
    if metaType == 'doi':
        metaDict = res.json()
        return (
            tuple((aDict['given'], aDict['family'])
                  for aDict in metaDict['author']),
            metaDict['title']
        )
    elif metaType == 'arxiv':
        aStr = '{http://www.w3.org/2005/Atom}'
        xmlEntryRoot = eTree.fromstring(res.text).find(f'{aStr}entry')
        return (
            tuple(tuple(ele.text.rsplit(' ', 1))
                  for ele
                  in xmlEntryRoot.findall(f'{aStr}author/{aStr}name')),
            re.sub('\\s+',
                   ' ',
                   xmlEntryRoot.find(f'{aStr}title').text.replace('\n', ''))
        )
    else:
        raise ValueError(f"Unknown metaType {metaType}")


if args.dir is None:
    args.dir = pathlib.Path.cwd()
else:
    # TODO better check this in dl stage?
    try:
        joinedDir = pathlib.Path.cwd() / pathlib.Path(args.dir).expanduser()
        args.dir = joinedDir.resolve(strict=True)
        if not args.dir.is_dir():
            raise FileNotFoundError
    except FileNotFoundError:
        print(pcolors("ERROR:", 'ERROR'), end=' ')
        print(str(joinedDir), "is not a valid directory")
        quit(1)
verbosePrint(f"Download directory: {pcolors(str(args.dir), 'PATH')}")

if args.mirror is None:
    # apply default
    args.mirror = ("https://sci-hub.se/", )
    # print("No mirror provided")
    # quit(2)
else:
    args.mirror = tuple(
        # enforce https if not specified
        urlunparse(urlparse(mirrorURL, scheme="https"))
        for mirrorURL in args.mirror
    )

proxyDict = {'http': args.proxy, 'https': args.proxy} \
    if (args.proxy is not None and args.proxy != "") \
    else None
# check proxy
if proxyDict is not None:
    try:
        verbosePrint("Testing proxy ...")
        rq.get("https://example.com/",
               proxies=proxyDict,
               headers={'User-Agent': args.useragent})
    except (rq.exceptions.InvalidURL, rq.exceptions.ProxyError):
        print(f"{pcolors('ERROR:', 'ERROR')} Proxy config is invalid")
        quit(2)
    except rq.ConnectionError:
        print(f"{pcolors('ERROR:', 'ERROR')} Failed connecting to "
              "requested proxy")
        quit(3)
    except Exception as e:
        print(f"{pcolors('ERROR:', 'ERROR')} Unknown exception when testing "
              "proxy connectivity: ")
        print(e)
        quit(3)
    else:
        verbosePrint(f"Using proxy {args.proxy}")
else:
    print(f"{pcolors('WARNING:', 'WARNING')} No proxy configured")

# deciding query type
# TODO find better method
queryType = next((qType for qType in ('doi', 'arxiv')
                  if qType in args.doi.lower()),
                 'doi')
# TODO need to check if query string is indeed DOI string when cannot decide
# if queryType is None:
#     print(f"{pcolors('ERROR:', 'ERROR')} Cannot decide repo type")
#     quit(4)
verbosePrint(f"Query string type: {pcolors(queryType, 'DOI')}")
reDOISanitizePattern, metaQueryURL, reqHeader = {
    'doi': (
        '^(https?://)?(dx\\.|www\\.)?doi(\\.org/|:|/)\\s*',
        'https://doi.org/{id}',
        {"Accept": "application/vnd.citationstyles.csl+json"}
    ),
    'arxiv': (
        '^(https?://)?arxiv(\\.org/abs/|:)?\\s*',
        'http://export.arxiv.org/api/query?id_list={id}',
        None
    )
}.get(queryType)

args.doi = re.sub(reDOISanitizePattern,
                  '',
                  args.doi.strip(),
                  flags=re.IGNORECASE)
verbosePrint(f"Sanitized query: {pcolors(args.doi, 'DOI')}")
metaQueryRes = rq.get(metaQueryURL.format(id=args.doi),
                      headers=reqHeader)
if not checkMetaInfoResponseValidity(metaQueryRes, queryType):
    print(f"{pcolors('ERROR:', 'ERROR')} Failed to resolve input DOI "
          f"{pcolors(args.doi, 'DOI')}")
    quit(4)

if args.output is None and args.autoname:
    metaDataTuple = getMetaInfoFromResponse(metaQueryRes, queryType)
    verbosePrint(f"author string: {metaDataTuple[0]}")
    verbosePrint(f"title string: {metaDataTuple[1]}")
    args.output = sanitizeString(
        f"[{transformToAuthorStr(metaDataTuple[0])}, "
        f"{queryType} {args.doi.replace('/', '@')}]"
        + transformToTitle(metaDataTuple[1])
    )
    print("Autopatched title: " + pcolors(args.output, 'PATH'))


def getTargetFileHandle(
    dlDir: pathlib.Path,
    targetURL: str,
    decidedFilename: Union[None, str]
) -> Union[BinaryIO, bool]:
    if decidedFilename is None:
        decidedFilename = urlparse(targetURL).path.rsplit('/', 1)[-1]
    else:
        decidedFilename = decidedFilename + '.' + targetURL.rsplit('.', 1)[-1]
    dlPath = dlDir / decidedFilename
    if len(str(dlPath)) >= 250:
        print(pcolors("ERROR:", 'ERROR'), end=" ")
        print("Cannot download to path exceeding 250 characters")
        return False
    verbosePrint(f"Downloading to {pcolors(str(dlPath), 'PATH')}")
    try:
        fHandle = dlPath.open('wb')
    except (PermissionError, FileNotFoundError):
        # TODO better handling of exceptions
        print(pcolors("ERROR:", 'ERROR'), end=" ")
        print("Cannot write to "
              f"target path \"{pcolors(str(dlPath), 'PATH')}\"")
        return False
    return fHandle


def downloadFileToPath(targetURL: str,
                       openedFileHandle: BinaryIO,
                       rqGetKwargDict: dict) -> bool:
    # assumed openedFileHandle is opened and valid for writing
    # openedFileHandle is automatically closed
    # TODO exception handling?
    downloadedSize = 0
    lastLineLen = 0
    dlMsg = None
    verbosePrint(f"Downloading from {pcolors(targetURL, 'PATH')} ...")
    with rq.get(targetURL, stream=True, **rqGetKwargDict) as dlResponse:
        fileSize = dlResponse.headers.get('Content-Length', None)
        if fileSize is not None:
            fileSize = int(fileSize)
            print("File size: " + humanByteUnitString(fileSize))
        else:
            print("File size unknown")
        with openedFileHandle:
            for dataChunk in dlResponse.iter_content(chunk_size=args.chunk):
                openedFileHandle.write(dataChunk)
                downloadedSize += len(dataChunk)
                if fileSize is not None:
                    dlMsg = "Downloaded " \
                        + f"{downloadedSize / fileSize * 100 :.2f}% " \
                        + f"({humanByteUnitString(downloadedSize)})"
                else:
                    dlMsg = "Downloaded " \
                        + humanByteUnitString(downloadedSize)
                print(dlMsg, end='')
                lenDLMsg = len(dlMsg)
                print(" " * (lastLineLen - lenDLMsg), end='\r')
                lastLineLen = lenDLMsg
    print("\nDownload done")
    return True


def getArXivRecordURL(identifierStr: str, mirrorURL: str) -> str:
    # TODO check if alright
    return urljoin(mirrorURL, identifierStr + '.pdf')


# TODO check if different mirrors have different response link
# TODO find better regex pattern
reDOIExtractPattern = re.compile(
    "\"location\\.href=.?'(.+?)\\?.*?download=true"
)


def getDOIRecordURL(identifierStr: str, mirrorURL: str) -> str:
    verbosePrint("Checking if mirror is online ...")
    try:
        if rq.get(mirrorURL,
                  proxies=proxyDict,
                  headers={'User-Agent': args.useragent}).status_code != 200:
            raise rq.exceptions.ConnectionError
    except (rq.exceptions.MissingSchema,
            rq.exceptions.InvalidSchema,
            rq.exceptions.InvalidURL):
        print(pcolors("ERROR:", 'ERROR'), end=" ")
        print(f"{mirrorURL} does not seem valid")
        return False
    except rq.exceptions.ConnectionError:
        print(pcolors("ERROR:", 'ERROR'), end=" ")
        print(f"Cannot connect to {mirrorURL}")
        return False
    # query mirror
    thisQueryURL = urljoin(mirrorURL, identifierStr)
    verbosePrint("Querying "
                 + pcolors(thisQueryURL, 'PATH')
                 + " ...")
    firstResponse = rq.get(thisQueryURL,
                           proxies=proxyDict,
                           headers={'User-Agent': args.useragent})
    # TODO better method of checking first return
    if (not firstResponse.headers['Content-Type'].startswith('text/html')) \
            or len(firstResponse.text.strip('\n ')) == 0:
        print(f"{pcolors('ERROR:', 'ERROR')} Empty response. "
              "Maybe no search result?")
        return False
    # extract download link
    verbosePrint("Findind download link from response ...")
    possibleDLLinkLst = list()
    for line in firstResponse.text.splitlines():
        # TODO better method of extracting download link
        # TODO better de-escaping url
        # enforce https if no scheme
        if 'download=true' in line:
            verbosePrint(line, 2)
            dlURL = urlunparse(
                urlparse(reDOIExtractPattern.search(line).group(1)
                         .replace(r'\\', '\\').replace(r'\/', '/'),
                         scheme="https")
            ).rsplit("#")[0]
            verbosePrint(f"Link found: {pcolors(dlURL, 'PATH')}")
            possibleDLLinkLst.append(dlURL)
    if len(possibleDLLinkLst) == 0:
        print(pcolors("ERROR:", 'ERROR'))
        print("No download link detected in response. \n"
              "Response format is not understood, "
              "or file may no be available on this mirror.")
        return False
    elif len(possibleDLLinkLst) > 1:
        print(pcolors("WARNING:", 'WARNING'))
        print("Multiple download links found. \n"
              "They are: ")
        for lnk in possibleDLLinkLst:
            print(lnk)
        print(f"{pcolors('WARNING:', 'WARNING')} Using only the first link")
        possibleDLLinkLst = possibleDLLinkLst[:1]
    return possibleDLLinkLst[0]


def fetchRecFromMirror(recIdentifier: str,
                       mirrorURL: str,
                       recURLFetcher: Callable[str, str],
                       rqGetKwargDict: dict) -> bool:
    docURL = recURLFetcher(recIdentifier, mirrorURL)
    fileHandle = getTargetFileHandle(args.dir,
                                     docURL,
                                     args.output)
    if fileHandle is False:
        quit(1)
    else:
        return downloadFileToPath(docURL,
                                  fileHandle,
                                  rqGetKwargDict)


if queryType == 'doi':
    if not any(fetchRecFromMirror(args.doi,
                                  mirrorURL,
                                  getDOIRecordURL,
                                  {'proxies': proxyDict,
                                   'headers': {'User-Agent': args.useragent}})
               for mirrorURL
               in args.mirror):
        print(f"{pcolors('Download failed:', 'ERROR')} no mirror seems to "
              "have this document")
        quit(5)
elif queryType == 'arxiv':
    if not fetchRecFromMirror(args.doi,
                              'https://arxiv.org/pdf/',
                              getArXivRecordURL,
                              {}):
        print(f"{pcolors('Download failed:', 'ERROR')} unable to fetch "
              "this document from arXiv")
        quit(5)
