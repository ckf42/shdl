from urllib.parse import urljoin
from xml.etree import ElementTree as eTree
from re import match as re_match
from re import IGNORECASE
import requests as rq

from ..CommonUtil import *
from ._BaseRepoHandler import _BaseRepoHandler


class ArxivRepoHandler(_BaseRepoHandler):
    repo_name = "arXiv"
    query_extract_pattern \
        = r'^(https?://)?arxiv(\.org/(abs|pdf)/|:)?\s*(.+)(\.pdf)?$'
    mirror_list = ('https://arxiv.org/pdf/',)

    @classmethod
    def get_identifier(cls, raw_query_str):
        match_gp = re_match(cls.query_extract_pattern,
                            raw_query_str,
                            flags=IGNORECASE)
        if match_gp:
            return match_gp.group(4)
        else:
            info_print(f"{PColor.WARNING('Failed')} parsing identifier as "
                       f"type {PColor.INFO(cls.repo_name)}")
            return None

    @classmethod
    def _is_meta_query_response_valid(cls, response_obj):
        console_print("Return status code: " + str(response_obj.status_code),
                      msg_verbose_level=VerboseLevel.DEBUG)
        return response_obj.status_code == 200 \
               and 'http://arxiv.org/api/errors' not in response_obj.text

    def get_metadata_response(self):
        console_print(f"{PColor.INFO('Fetching metadata')} "
                      f"for type {PColor.INFO(self.repo_name)}...",
                      msg_verbose_level=VerboseLevel.VERBOSE)
        return rq.get(
            'http://export.arxiv.org/api/query?id_list={id}'.format(
                id=self.identifier
            ),
            **cliArg['rqKwargs']
        )

    def extract_metadata(self):
        if not self._is_meta_query_response_valid(self.metadata_response):
            info_print(f"Response is not a valid {self.repo_name} response")
            return False
        atom_str = '{http://www.w3.org/2005/Atom}'
        entry_root = eTree.fromstring(self.metadata_response.text) \
            .find(f'{atom_str}entry')
        return {
            'author': tuple(dict(zip(('given', 'family'),
                                     ele.text.strip().rsplit(' ', 1)))
                            for ele
                            in entry_root
                            .findall(f'{atom_str}author/{atom_str}name')),
            'title':  ' '.join(entry_root.find(f'{atom_str}title')
                               .text.split(None)),
            'year':   entry_root.find(f'{atom_str}updated').text[:4],
        }

    def get_download_url(self, mirror_link):
        return urljoin(mirror_link, self.identifier + '.pdf')
