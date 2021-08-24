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

    @classmethod
    def get_identifier(cls, raw_query_str):
        match_gp = re_match(cls.get_query_extract_pattern(),
                            raw_query_str,
                            flags=IGNORECASE)
        if match_gp:
            return match_gp.group(4)
        else:
            return None

    @classmethod
    def get_mirror_list(cls) -> tuple[str]:
        return 'https://arxiv.org/pdf/',

    @classmethod
    def get_repo_name(cls):
        return "arXiv"

    @classmethod
    def get_download_url(
            cls,
            identifier_str,
            mirror_link,
            **kwargs
    ):
        return urljoin(mirror_link, identifier_str + '.pdf')

    @classmethod
    def get_metadata(cls, identifier_str):
        meta_query_res = rq.get(
            'http://export.arxiv.org/api/query?id_list={id}'
                .format(id=identifier_str)
        )
        if not cls.is_meta_query_response_valid(meta_query_res):
            return False
        atom_str = '{http://www.w3.org/2005/Atom}'
        entry_root = eTree.fromstring(meta_query_res.text) \
            .find(f'{atom_str}entry')
        return {
            'author': tuple(
                dict(zip(('given', 'family'),
                         ele.text.rsplit(' ', 1)))
                for ele
                in entry_root
                    .findall(f'{atom_str}author/{atom_str}name')),
            'title':  ' '.join(entry_root.find(f'{atom_str}title')
                               .text.split(None))
        }

    @classmethod
    def is_meta_query_response_valid(cls, response_obj):
        return response_obj.status_code == 200 \
               and 'http://arxiv.org/api/errors' not in response_obj.text

    @classmethod
    def get_query_extract_pattern(cls):
        return r'^(https?://)?arxiv(\.org/(abs|pdf)/|:)?\s*(.+)(\.pdf)?$'
