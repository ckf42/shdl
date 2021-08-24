from urllib.parse import urljoin
from xml.etree import ElementTree as eTree
from re import match as re_match
from re import IGNORECASE
import requests as rq

from src.RepoHandler._BaseRepoHandler import _BaseRepoHandler
from src.CommonUtil import *

if __name__ == '__main__':
    quit()


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
            verbose_print(f"Failed parsing identifier as type {cls.repo_name}")
            return None

    @classmethod
    def is_meta_query_response_valid(cls, response_obj):
        return response_obj.status_code == 200 \
               and 'http://arxiv.org/api/errors' not in response_obj.text

    def get_metadata(self):
        meta_query_res = rq.get(
            'http://export.arxiv.org/api/query?id_list={id}'
                .format(id=self.identifier)
        )
        if not self.is_meta_query_response_valid(meta_query_res):
            verbose_print(f"Response is not a valid {self.repo_name} response")
            return False
        atom_str = '{http://www.w3.org/2005/Atom}'
        entry_root = eTree.fromstring(meta_query_res.text) \
            .find(f'{atom_str}entry')
        return {
            'author': tuple(dict(zip(('given', 'family'),
                                     ele.text.rsplit(' ', 1)))
                            for ele
                            in entry_root
                            .findall(f'{atom_str}author/{atom_str}name')),
            'title':  ' '.join(entry_root.find(f'{atom_str}title')
                               .text.split(None))
        }

    def get_download_url(self, mirror_link, **kwargs):
        return urljoin(mirror_link, self.identifier + '.pdf')
