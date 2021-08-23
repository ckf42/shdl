from urllib.parse import urljoin
from xml.etree import ElementTree as eTree

import requests as rq

from _BaseRepoHandler import _BaseRepoHandler
from CommonUtil import *


class ArxivRepoHandler(_BaseRepoHandler):

    @classmethod
    def get_repo_name(cls):
        return "arXiv"

    @classmethod
    def get_download_url(
            cls,
            identifier_str,
            mirror_link='https://arxiv.org/pdf/',
            **kwargs
            ):
        return urljoin(mirror_link, identifier_str)

    @classmethod
    def fetch_metadata(cls, identifier_str):
        meta_query_res = rq.get(cls.get_query_sanitizer_string()
                                .format(id=identifier_str))
        if not cls.is_meta_query_response_valid(meta_query_res):
            return None
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
    def get_query_sanitizer_string(cls):
        return '^(https?://)?arxiv(\\.org/abs/|:)?\\s*'