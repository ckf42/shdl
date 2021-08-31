import requests as rq

from urllib.parse import urljoin, urlparse, urlunparse
from re import match as re_match
from re import search as re_search
from re import sub as re_sub
from re import compile as re_compile
from re import findall as re_findall
from re import IGNORECASE, MULTILINE
from html import unescape, escape
from unicodedata import category as ud_category
from unicodedata import name as ud_name
from xml.etree import ElementTree as eTree
from typing import Union

from ..CommonUtil import *
from ._BaseRepoHandler import _BaseRepoHandler

if __name__ == '__main__':
    quit()


class DOIRepoHandler(_BaseRepoHandler):
    repo_name = "DOI"
    query_extract_pattern \
        = (r'^(https?://)?((www\.|dx\.)?doi(\.org)?|'
           r'(link\.)?springer(\.com/(\w+))?)'
           r'(:|/)?\s*(.+)$')
    mirror_list = cliArg['mirror']

    # TODO change into a class property?
    link_extractor = re_compile(
        "\"location\\.href=.?'(.+?)\\?.*?download=true",
        flags=IGNORECASE
    )
    aims_extractor = re_compile(
        '^\\s*<meta name="citation_pdf_url" '
        'content="https://www\\.aimsciences\\.org/article/'
        'exportPdf\\?id=(.+?)"/>\\s*$',
        flags=IGNORECASE
    )
    aims_xml_sanitizer = re_compile('\\s*<(.+?)>(.+?)</\\1>\\s*',
                                    flags=IGNORECASE | MULTILINE)

    # Why is this a class method?
    # TODO check if this has to be a class method
    @classmethod
    def get_identifier(cls, raw_query_str):
        match_gp = re_match(cls.query_extract_pattern,
                            raw_query_str,
                            flags=IGNORECASE)
        if match_gp:
            return match_gp.group(9)
        else:
            info_print(f"Failed parsing identifier as type {cls.repo_name}")
            return None

    @classmethod
    def _is_meta_query_response_valid(cls, response_obj):
        return response_obj.status_code == 200 \
               and response_obj.headers['content-type'] \
               == 'application/vnd.citationstyles.csl+json'

    def get_metadata_response(self):
        info_print(f"Fetching metadata for type {self.repo_name}...")
        return rq.get(
            'https://doi.org/{id}'.format(id=self.identifier),
            headers={"Accept": "application/vnd.citationstyles.csl+json"}
        )

    def extract_metadata(self):
        if not self._is_meta_query_response_valid(self.metadata_response):
            info_print(f"Response is not a valid {self.repo_name} response")
            return False
        meta_json_dict = self.metadata_response.json()
        if all(k in meta_json_dict for k in ('author', 'title')) \
                and all(all(k in aDict for k in ('given', 'family'))
                        for aDict in meta_json_dict['author']):
            doc_title \
                = ''.join((f' {ud_name(c).title()}'
                           if not c.isascii() and ud_category(c) == 'Sm'
                           else c)
                          for c in re_sub('</?.+?>',
                                          '',
                                          unescape(meta_json_dict['title'])))
            publish_year = str(''
                               if (pDict := meta_json_dict
                                   .get('published-print', None)) is None
                               else pDict.get('date-parts', [['']])[0][0])
            return {
                'author': tuple({k: aDict[k].strip()
                                 for k in ('given', 'family')}
                                for aDict in meta_json_dict['author']),
                'title':  doc_title,
                'year':   publish_year
            }
        # DOI does not return enough metadata
        info_print(PColor.WARNING("WARNING:"), end=" ")
        info_print("DOI query does not return enough metadata. "
                   "Trying alternative methods ...")
        alt_metadata = self.alt_extract_metadata()
        if alt_metadata is None:
            info_print(PColor.ERROR("Error:"), end=" ")
            info_print("Response does not have enough metadata. "
                       "Please report this DOI as a bug")
        return alt_metadata

    def get_download_url(self,
                         mirror_link,
                         identifier_override: Optional[str] = None):
        """
        Get file download link

        Returns the direct download link to the file.
        If unable to get the download link, returns None

        :param mirror_link: str.
            The URL of the mirror used to fetch the file
        :param identifier_override: Optional[str].
            The path used for querying mirror.
            If None, will use self.identifier
        :return: str, or None.
        """

        # test mirror
        if identifier_override is None:
            identifier_override = self.identifier
        console_print("Checking if mirror "
                      + PColor.PATH(mirror_link)
                      + " is online ...",
                      msg_verbose_level=VerboseLevel.VERBOSE)
        try:
            if rq.get(mirror_link, **cliArg['rqKwargs']).status_code != 200:
                raise rq.exceptions.ConnectionError
        except (rq.exceptions.MissingSchema,
                rq.exceptions.InvalidSchema,
                rq.exceptions.InvalidURL):
            info_print(PColor.ERROR("ERROR:"), end=" ")
            info_print(f"{mirror_link} does not seem valid")
            return None
        except rq.exceptions.ConnectionError:
            info_print(PColor.ERROR("ERROR:"), end=" ")
            info_print(f"Cannot connect to {mirror_link}. "
                       "Maybe it is not online (for you)?")
            return None

        # query mirror
        query_url = urljoin(mirror_link, identifier_override)
        console_print("Querying " + PColor.PATH(query_url) + " ...",
                      msg_verbose_level=VerboseLevel.VERBOSE)
        preview_resp = rq.get(query_url, **cliArg['rqKwargs'])
        if (not preview_resp.headers['Content-Type'].startswith('text/html')) \
                or len(preview_resp.text.strip('\n ')) == 0:
            info_print(PColor.ERROR("ERROR:"), end=" ")
            info_print("Response is empty. Perhaps no search result? ")
            return None

        # parse response
        console_print("Finding download link ...",
                      msg_verbose_level=VerboseLevel.DEBUG)
        possible_link = list()
        for line in preview_resp.text.splitlines():
            line = unescape(line).strip()
            if (match_obj := self
                    .link_extractor.search(line, IGNORECASE)) is not None:
                console_print(f"Line with possible link: {line}",
                              msg_verbose_level=VerboseLevel.DETAIL)
                dl_url = urlunparse(
                    urlparse(match_obj.group(1)
                             .rsplit('#', 1)[0]  # rm fragment
                             .replace(r'\/', '/'),  # unescape \/
                             scheme='https'))  # force scheme if missing
                console_print("Link found: " + PColor.PATH(dl_url),
                              msg_verbose_level=VerboseLevel.VERBOSE)
                possible_link.append(dl_url)
        if len(possible_link) == 0:
            info_print(PColor.ERROR("ERROR:"), end=" ")
            info_print("No download link found. "
                       "File not available, or response format not understood")
            return None
        elif len(possible_link) > 1:
            info_print(PColor.WARNING("WARNING: "), end=" ")
            info_print("More than one link found. They are: ")
            for link in possible_link:
                info_print(PColor.PATH(link))
            info_print("Using only the first link")
            possible_link = possible_link[:1]
        return possible_link[0]

    def alt_extract_metadata_jstor(self) -> Union[bool, dict, None]:
        """
        Alternative method to get metadata from JSTOR.
        Also set self.metadata_response

        :return: bool (False), None or dict.
            Same as self.extract_metadata
        """
        query_url = 'https://www.jstor.org/citation/ris/{id}'.format(
            id=self.identifier)
        console_print(f"Fetching from {PColor.PATH(query_url)}",
                      msg_verbose_level=VerboseLevel.INFO)
        jstor_resp = rq.get(query_url, **cliArg['rqKwargs'])
        self.metadata_response = jstor_resp
        if jstor_resp.status_code == 200 \
                and jstor_resp.headers['Content-Type'] \
                .startswith('application/x-research-info-systems'):
            auth_list = list()
            doc_title = None
            publish_year = ''
            for line in jstor_resp.text.splitlines():
                if line.startswith('AU  -'):  # author line
                    auth_list.append(line[6:])
                elif line.startswith('TI  -'):  # title line
                    doc_title = line[6:]
                elif line.startswith('PY  - '):  # publish year
                    publish_year = line[6:]
            if len(auth_list) != 0 and doc_title is not None:
                # able to get the needed information
                return {
                    # not sure if RIS always put family name first
                    # may have seen counter-example?
                    'author': tuple(dict(zip(('family', 'given'),
                                             aItem.strip().rsplit(', ', 1)))
                                    for aItem in auth_list),
                    'title':  doc_title,
                    'year':   publish_year,
                }
            else:
                # even citation record is incomplete
                return None
        else:
            info_print(PColor.ERROR("ERROR:"), end=" ")
            info_print("Unable to fetch metadata from JSTOR. "
                       "Maybe JSTOR blocked the requests?")
            return False

    def alt_extract_metadata_aims(self) -> Union[bool, dict, None]:
        """
        Alternative method to get metadata from AIMS.
        Also set self.metadata_response

        :return: bool (False), None or dict.
            Same as self.extract_metadata
        """
        query_url = 'https://www.aimsciences.org/article/doi/{id}'.format(
            id=self.identifier)
        info_print(f"Fetching from {PColor.PATH(query_url)}")
        aims_resp = rq.get(query_url, headers=cliArg['rqKwargs']['headers'])
        # TODO check valid
        aims_internal_id = None
        for line in aims_resp.text.splitlines():
            if (match_obj := self.aims_extractor.search(line)) is not None:
                aims_internal_id = match_obj.group(1)
                break
        if aims_internal_id is None:
            info_print(PColor.ERROR("ERROR:"), end=" ")
            info_print("Failed to parse AIMS response")
            return False
        console_print(f"AIMS ID: {aims_internal_id}",
                      msg_verbose_level=VerboseLevel.VERBOSE)
        xml_resp = rq.get(
            'https://www.aimsciences.org/article/'
            'exportXML?ids={id}&downType=XML'.format(
                id=aims_internal_id),
            **cliArg['rqKwargs']
        )
        self.metadata_response = xml_resp
        # TODO check valid
        xml_root = eTree.fromstring(
            self.aims_xml_sanitizer.sub(
                lambda x: (f'<{x.group(1)}>'
                           f'{escape(x.group(2))}'
                           f'</{x.group(1)}>'),
                xml_resp.text))
        return {
            'author': tuple(dict(zip(('given', 'family'),
                                     aItem.text.strip().rsplit(' ', 1)))
                            for aItem
                            in xml_root
                            .findall('record/authors/author/name')),
            'title':  xml_root.find('record/title').text.strip(),
            'year':   (''
                       if (pDate := xml_root
                           .find('record/publicationDate')) is None
                       else pDate.text.strip()[:4])
        }

    def alt_extract_metadata_royalsocpub(self) -> Union[bool, dict, None]:
        """
        Alternative method to get metadata from Royal Society Publishing.
        Also set self.metadata_response

        :return: bool (False), None or dict.
            Same as self.extract_metadata
        """
        query_url = 'https://royalsocietypublishing.org/doi/{id}'.format(
            id=self.identifier)
        console_print(f"Fetching from {PColor.PATH(query_url)}",
                      msg_verbose_level=VerboseLevel.INFO)
        royal_resp = rq.get(query_url, headers=cliArg['rqKwargs']['headers'])
        # PaRsInG HtMl wItH rEgEx !!!1!11!!!
        # TODO need better method
        article_title = (
            match_obj.group(1)
            if (match_obj := re_search(
                r'<meta name="dc\.Title" content="(.+?)">',
                royal_resp.text)) is not None
            else None
        )
        author_list = re_findall(
            r'<span class="hlFld-ContribAuthor">\s*<a.+?title="(.+?)">',
            royal_resp.text
        )
        pub_year = (
            match_obj.group(1)
            if (match_obj := re_search(
                r'<meta name="dc\.Date".+content="(\d{4})-\d{2}-\d{2}">',
                royal_resp.text,
                flags=IGNORECASE)) is not None
            else ''
        )
        if article_title is not None and len(author_list) != 0:
            return {
                'author': tuple(dict(zip(('family', 'given'),
                                         authorStr.strip().split(' ', 1)))
                                for authorStr in author_list),
                'title':  article_title,
                'year':   pub_year
            }
            pass
        else:
            # even webpage record is incomplete
            return None

    def alt_extract_metadata(self) -> Union[bool, dict, None]:
        """
        Alternative method to get metadata.

        :return: bool (False), None or dict.
            Same as self.extract_metadata
        """
        # get doc host
        self_host = urlparse(rq.get('https://doi.org/{id}'
                                    .format(id=self.identifier)).url).netloc
        console_print(f"Document host: {self_host}",
                      msg_verbose_level=VerboseLevel.VERBOSE)
        metadata_getter_func = {
            'www.jstor.org':       self.alt_extract_metadata_jstor,
            'www.aimsciences.org': self.alt_extract_metadata_aims,
            'royalsocietypublishing.org':
                                   self.alt_extract_metadata_royalsocpub,
        }.get(self_host, None)
        if metadata_getter_func is None:
            info_print(PColor.ERROR("ERROR:"), end=" ")
            info_print(f"{self_host} is not a recognized host. "
                       "Please report this on main page")
            return False
        else:
            return metadata_getter_func()
