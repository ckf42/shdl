import requests as rq

from urllib.parse import urljoin

from _BaseRepoHandler import _BaseRepoHandler
from CLIArgParser import cliArg


class DOIRepoHandler(_BaseRepoHandler):
    @property
    @classmethod
    def user_agent_str(cls):
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) "\
                    "Gecko/20100101 Firefox/78.0"
    @classmethod
    def get_download_url(cls, identifier_str, mirror_link, **kwargs):
        first_response = rq.get(urljoin(mirror_link, identifier_str),
                                headers=kwargs.get('headers', {'User-Agent': cls.user_agent_str}))
        if not first_response.headers['Content-Type'].startswith('text/html') or len(first_response.text.strip('\n ') == 0):
            return None

    @classmethod
    def get_query_sanitizer_string(cls):
        return '^(https?://)?(dx\\.|www\\.)?doi(\\.org/|:|/)\\s*'

    @classmethod
    def fetch_metadata(cls, identifier_str):
        meta_query_res = rq.get(
                cls.get_query_sanitizer_string().format(id=identifier_str),
                headers={"Accept": "application/vnd.citationstyles.csl+json"}
                )
        if not cls.is_meta_query_response_valid(meta_query_res):
            return None
        meta_dict = meta_query_res.json()
        return {
                'author': tuple(
                        {'family': aDict['family'], 'given': aDict['given']}
                        for aDict in meta_dict['author']
                        ),
                'title':  meta_dict['title']
                }

    @classmethod
    def is_meta_query_response_valid(cls, response_obj):
        return response_obj.status_code == 200 \
               and response_obj.headers['content-type'] \
               == 'application/vnd.citationstyles.csl+json'