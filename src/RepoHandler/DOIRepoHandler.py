import requests as rq

from urllib.parse import urljoin, urlparse, urlunparse
from re import match as re_match
from re import sub as re_sub
from re import compile as re_compile
from re import IGNORECASE, MULTILINE
from html import unescape, escape
from unicodedata import category as ud_category
from unicodedata import name as ud_name
from xml.etree import ElementTree as eTree
from typing import Union

from src.RepoHandler._BaseRepoHandler import _BaseRepoHandler
from src.CLIArgParser import *
from src.CommonUtil import *

if __name__ == '__main__':
    quit()


class DOIRepoHandler(_BaseRepoHandler):
    repo_name = "DOI"
    query_extract_pattern \
        = r'^(https?://)?(dx\.|www\.)?doi(\.org/|:|/)\s*(.+)$'
    mirror_list = cliArg.mirror

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

    @classmethod
    def get_identifier(cls, raw_query_str):
        match_gp = re_match(cls.query_extract_pattern,
                            raw_query_str,
                            flags=IGNORECASE)
        if match_gp:
            return match_gp.group(4)
        else:
            verbose_print(f"Failed parsing identifier as type {cls.repo_name}")
            return None

    @classmethod
    def _is_meta_query_response_valid(cls, response_obj):
        return response_obj.status_code == 200 \
               and response_obj.headers['content-type'] \
               == 'application/vnd.citationstyles.csl+json'

    def get_metadata_response(self):
        verbose_print(f"Fetching metadata for type {self.repo_name}...")
        return rq.get(
            'https://doi.org/{id}'.format(id=self.identifier),
            headers={"Accept": "application/vnd.citationstyles.csl+json"}
        )

    def extract_metadata(self):
        if not self._is_meta_query_response_valid(self.metadata_response):
            verbose_print(f"Response is not a valid {self.repo_name} response")
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
            return {
                'author': tuple({k: aDict[k] for k in ('given', 'family')}
                                for aDict in meta_json_dict['author']),
                'title':  doc_title
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

    def get_download_url(self, mirror_link):
        # test mirror
        verbose_print("Checking if mirror "
                      + PColor.PATH(mirror_link)
                      + " is online ...")
        try:
            if rq.get(mirror_link, **cliArg.rqKwargs).status_code != 200:
                raise rq.exceptions.ConnectionError
        except (rq.exceptions.MissingSchema,
                rq.exceptions.InvalidSchema,
                rq.exceptions.InvalidURL):
            info_print(PColor.ERROR("ERROR:"), end=" ")
            info_print(f"{mirror_link} does not seem valid")
            return None
        except rq.exceptions.ConnectionError:
            info_print(PColor.ERROR("ERROR:"), end=" ")
            info_print(f"Cannot connect to {mirror_link}")
            return None

        # query mirror
        query_url = urljoin(mirror_link, self.identifier)
        verbose_print("Querying " + PColor.PATH(query_url) + " ...")
        preview_resp = rq.get(query_url, **cliArg.rqKwargs)
        if (not preview_resp.headers['Content-Type'].startswith('text/html')) \
                or len(preview_resp.text.strip('\n ')) == 0:
            info_print(PColor.ERROR("ERROR:"), end=" ")
            info_print("Response is empty. Perhaps no search result? ")
            return None

        # parse response
        verbose_print("Finding download link ...")
        possible_link = list()
        for line in preview_resp.text.splitlines():
            line = unescape(line)
            if (match_obj \
                    := self.link_extractor.search(line,
                                                  IGNORECASE)) is not None:
                verbose_print(f"Line with possible link: {line}", 2)
                dl_url = urlunparse(
                    urlparse(match_obj.group(1).rsplit('#', 1)[0],
                             scheme='https'))
                verbose_print("Link found: " + PColor.PATH(dl_url))
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

        :return: bool (False), None or dict.
            Same as self.extract_metadata
        """
        query_url = 'https://www.jstor.org/citation/ris/{id}'.format(
            id=self.identifier)
        verbose_print(f"Fetching from {PColor.PATH(query_url)}")
        jstor_resp = rq.get(query_url, **cliArg.rqKwargs)
        if jstor_resp.status_code == 200 \
                and jstor_resp.headers['Content-Type'] \
                == 'application/x-research-info-systems':
            auth_list = list()
            doc_title = None
            for line in jstor_resp.text.splitlines():
                if line.startswith('AU  -'):  # author line
                    auth_list.append(line[6:])
                elif line.startswith('TI  -'):  # title line
                    doc_title = line[6:]
            if len(auth_list) != 0 and doc_title is not None:
                # able to get the needed information
                return {
                    'author': tuple(dict(zip(('given', 'family'),
                                             aItem.rsplit(', ', 1)))
                                    for aItem in auth_list),
                    'title':  doc_title
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

        :return: bool (False), None or dict.
            Same as self.extract_metadata
        """
        query_url = 'https://www.aimsciences.org/article/doi/{id}'.format(
            id=self.identifier)
        verbose_print(f"Fetching from {PColor.PATH(query_url)}")
        aims_resp = rq.get(query_url, headers=cliArg.rqKwargs['headers'])
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
        verbose_print(f"AIMS ID: {aims_internal_id}")
        xml_resp = rq.get(
            'https://www.aimsciences.org/article/'
            'exportXML?ids={id}&downType=XML'.format(
                id=aims_internal_id),
            **cliArg.rqKwargs
        )
        # TODO check valid
        xml_root = eTree.fromstring(
            self.aims_xml_sanitizer.sub(
                lambda x: (f'<{x.group(1)}>'
                           f'{escape(x.group(2))}'
                           f'</{x.group(1)}>'),
                xml_resp.text))
        return {
            'author': tuple(dict(zip(('given', 'family'),
                                     aItem.text.rsplit(' ', 1)))
                            for aItem
                            in xml_root
                            .findall('record/authors/author/name')),
            'title':  xml_root.find('record/title').text.strip()
        }

    def alt_extract_metadata(self) -> Union[bool, dict, None]:
        """
        Alternative method to get metadata.

        :return: bool (False), None or dict.
            Same as self.extract_metadata
        """
        # get doc host
        self_host = urlparse(rq.get('https://doi.org/{id}'
                                    .format(id=self.identifier)).url).netloc
        verbose_print(f"Document host: {self_host}")
        metadata_getter_func = {
            'www.jstor.org':       self.alt_extract_metadata_jstor,
            'www.aimsciences.org': self.alt_extract_metadata_aims
        }.get(self_host, None)
        if metadata_getter_func is None:
            info_print(PColor.ERROR("ERROR:"), end=" ")
            info_print(f"{self_host} is not a recognized host. "
                       "Please report this on main page")
            return False
        else:
            return metadata_getter_func()
