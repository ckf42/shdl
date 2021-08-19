# TODO use urllib.request instead?
import requests as rq
import re
from argparse import ArgumentParser as aAP
from urllib.parse import urljoin, urlunparse, urlparse
import pathlib
# TODO use unidecode instead?
from unicodedata import normalize as ucNormalize

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
                    version="%(prog)s v0.4.1 by KAC")
parser.add_argument("doi",
                    type=str,
                    help="The DOI string of the document. "
                    "If the string contains spaces, it must be quoted")
parser.add_argument("--proxy",
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
parser.add_argument("--dir",
                    type=str,
                    help="Download to this directory. "
                    "Relative path to current working directory. "
                    "May contain (Unix-style) ~ for home dir. "
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
                    "(TOR Browser on Win10 x64) "
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) "
                    "Gecko/20100101 Firefox/78.0")
parser.add_argument("--autoname",
                    action='store_true',
                    help="Automatically name the file by its DOI metadata. "
                    "May not give the best file name. "
                    "Format: [<authors>, doi <doi>]<title> "
                    "Has lower priority than --output")
parser.add_argument("--verbose", "-v",
                    action='count',
                    default=0,
                    help="Display verbose information")
args = parser.parse_args()


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
def titleCapitalize(s: str) -> str:
    wordsInSent = re.split('\\b', s)
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
        print(str(joinedDir), "is not a valid directory")
        quit()
verbosePrint(f"Download directory: {str(args.dir)}")

if args.mirror is None:
    # apply default
    args.mirror = ("https://sci-hub.se/", )
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
        print("Proxy config is invalid")
        quit()
    except rq.ConnectionError:
        print("Failed connecting to requested proxy")
        quit()
    except Exception as e:
        print("Unknown exception when testing proxy connectivity: ")
        print(e)
        quit()
    else:
        verbosePrint(f"Using proxy {args.proxy}")
else:
    print("WARNING: No proxy configured")

args.doi = re.sub("^(https?://)?(dx\\.|www\\.)?doi(\\.org/|:|/)\\s*",
                  '',
                  args.doi.strip())
doiRes = rq.get(
    urljoin('https://doi.org', args.doi),
    headers={"Accept": "application/vnd.citationstyles.csl+json"}
)
if doiRes.status_code != 200 \
    or doiRes.headers['content-type'] != ('application/'
                                          'vnd.citationstyles.csl+json'):
    print(f"Fail to resolve input DOI \"{args.doi}\"")
    quit()
verbosePrint(f"Input DOI: {args.doi}")

autoPatchedName = None
if args.output is not None:
    # priority surpress
    args.autoname = False
if args.autoname:
    metaDict = doiRes.json()
    authorStr = ', '.join(''.join((gNamePart
                                   if len(gNamePart) <= 1
                                   else gNamePart[0] + '.')
                                  for gNamePart
                                  in re.split(r'\b', authorDict['given']))
                          + ' '
                          + authorDict['family']
                          for authorDict in metaDict['author'])
    verbosePrint(f"author string: {authorStr}")
    autoPatchedName = sanitizeString(
        f"[{authorStr}, doi {args.doi.replace('/', ' ')}]"
        + titleCapitalize(re.sub('</?mml.+?>',
                                 '',
                                 metaDict['title'].strip(' ,."\'')))
    )
    print("Autopatched title: " + autoPatchedName)

# TODO check if different mirrors have different response link
# TODO find better regex pattern
rePattern = re.compile("\"location\\.href=.?'(.+?)\\?.*?download=true")


def tryFetchDocFromSciHubMirror(mirrorURL: str, docDOI: str) -> bool:
    verbosePrint("Checking if mirror is online ...")
    try:
        if rq.get(mirrorURL,
                  proxies=proxyDict,
                  headers={'User-Agent': args.useragent}).status_code != 200:
            raise rq.exceptions.ConnectionError
    except (rq.exceptions.MissingSchema,
            rq.exceptions.InvalidSchema,
            rq.exceptions.InvalidURL):
        print(f"{mirrorURL} does not seem valid")
        return False
    except rq.exceptions.ConnectionError:
        print(f"Cannot connect to {mirrorURL}")
        return False

    verbosePrint("Querying " + urljoin(mirrorURL, docDOI) + " ...")
    firstResponse = rq.get(urljoin(mirrorURL, docDOI),
                           proxies=proxyDict,
                           headers={'User-Agent': args.useragent})
    # TODO better method of checking first return
    if (not firstResponse.headers['Content-Type'].startswith('text/html')) \
            or len(firstResponse.text.strip('\n ')) == 0:
        print("Empty response. Maybe no search result?")
        return False

    verbosePrint("Findind download link from response ...")
    possibleDLLinkLst = list()
    for line in firstResponse.text.splitlines():
        # TODO better method of extracting download link
        # TODO better de-escaping url
        # enforce https if no scheme
        if 'download=true' in line:
            verbosePrint(line, 2)
            dlURL = urlunparse(
                urlparse(rePattern.search(line).group(1)
                         .replace(r'\\', '\\').replace(r'\/', '/'),
                         scheme="https")
            ).rsplit("#")[0]
            verbosePrint(f"Link found: {dlURL}")
            possibleDLLinkLst.append(dlURL)
    if len(possibleDLLinkLst) == 0:
        print("No download link detected in response. \n"
              "Response format is not understood, "
              "or file may no be available on this mirror.")
        return False
    elif len(possibleDLLinkLst) > 1:
        print("Multiple download links found. \n"
              "They are: ")
        for lnk in possibleDLLinkLst:
            print(lnk)
        print("Using only the first link")
        possibleDLLinkLst = possibleDLLinkLst[:1]
    docURL = possibleDLLinkLst[0]

    verbosePrint(f"Downloading from {docURL} ...")
    dlFilename = urlparse(docURL).path.rsplit('/', 1)[-1]
    if args.output is not None:
        dlFilename = args.output + '.' + dlFilename.rsplit('.')[-1]
    elif args.autoname:
        dlFilename = autoPatchedName + '.' + dlFilename.rsplit('.')[-1]
    dlTargetPath = args.dir / dlFilename
    verbosePrint(f"Downloading to {str(dlTargetPath)}")
    downloadedSize = 0
    lastLineLen = 0
    dlMsg = None
    try:
        fileHandle = dlTargetPath.open('wb')
    except PermissionError:
        # TODO better handling of exceptions
        print(f"Cannot write to target path \"{str(dlTargetPath)}\"")
        return False
    with rq.get(docURL,
                proxies=proxyDict,
                stream=True,
                headers={'User-Agent': args.useragent}) as dlResponse:
        fileSize = dlResponse.headers.get('Content-Length', None)
        if fileSize is not None:
            fileSize = int(fileSize)
            print("File size: " + humanByteUnitString(fileSize))
        else:
            print("File size unknown")
        with fileHandle:
            for dataChunk in dlResponse.iter_content(chunk_size=args.chunk):
                fileHandle.write(dataChunk)
                downloadedSize += len(dataChunk)
                if fileSize is not None:
                    dlMsg = "Downloaded " \
                        + f"{downloadedSize / fileSize * 100 :.2f}%"
                else:
                    dlMsg = "Downloaded " \
                        + humanByteUnitString(downloadedSize)
                print(dlMsg, end='')
                lenDLMsg = len(dlMsg)
                print(" " * (lastLineLen - lenDLMsg), end='\r')
                lastLineLen = lenDLMsg
    print("\nDownload done")
    return True


if not any(tryFetchDocFromSciHubMirror(mirrorURL, args.doi)
           for mirrorURL
           in args.mirror):
    print("Download failed: no mirror seems to have this document")
