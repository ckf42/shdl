import requests as rq

from urllib.parse import urljoin, urlparse, urlunparse
from re import match as re_match
from re import sub as re_sub
from re import compile as re_compile
from re import IGNORECASE
from html import unescape
from unicodedata import category as ud_category
from unicodedata import name as ud_name

from src.RepoHandler._BaseRepoHandler import _BaseRepoHandler
from src.CLIArgParser import *
from src.CommonUtil import *

if __name__ == '__main__':
    quit()


class DOIRepoHandler(_BaseRepoHandler):
    repo_name = "DOI"
    query_extract_pattern \
        = r'^(https?://)?(dx\.|www\.)?doi(\.org/|:|\/)\s*(.+)$'
    mirror_list = cliArg.mirror

    # TODO change into a class property?
    link_extracter = re_compile(
        "\"location\\.href=.?'(.+?)\\?.*?download=true")

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

    def get_metadata(self):
        verbose_print(f"Fetching metadata for type {self.repo_name}...")
        meta_query_res = rq.get(
            'https://doi.org/{id}'.format(id=self.identifier),
            headers={"Accept": "application/vnd.citationstyles.csl+json"}
        )
        if not self._is_meta_query_response_valid(meta_query_res):
            verbose_print(f"Response is not a valid {self.repo_name} response")
            return False
        meta_json = meta_query_res.json()
        return {
            'author': tuple({k: aDict[k] for k in ('given', 'family')}
                            for aDict in meta_json['author']),
            'title':  ''.join((f' {ud_name(c).title()}'
                               if not c.isascii() and ud_category(c) == 'Sm'
                               else c)
                              for c in re_sub('</?.+?>', '',
                                              unescape(meta_json['title'])))
        }

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
                    := self.link_extracter.search(line,
                                                  IGNORECASE)) is not None:
                verbose_print(f"Line with possible link: {line}", 2)
                dlURL = urlunparse(
                    urlparse(match_obj.group(1).rsplit('#', 1)[0],
                             scheme='https'))
                verbose_print("Link found: " + PColor.PATH(dlURL))
                possible_link.append(dlURL)
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