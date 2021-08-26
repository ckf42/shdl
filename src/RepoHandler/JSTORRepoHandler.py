from re import match as re_match
from re import IGNORECASE

from src.CLIArgParser import *
from src.CommonUtil import *
from src.RepoHandler.DOIRepoHandler import *

if __name__ == '__main__':
    quit()


class JSTORRepoHandler(DOIRepoHandler):
    repo_name = "JSTOR"
    query_extract_pattern \
        = r'^(https?://)?(www\.)?jstor(\.org/stable/|:)?\s*(.+)$'
    mirror_list = cliArg['mirror']

    extract_metadata = DOIRepoHandler.alt_extract_metadata_jstor

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
               and response_obj.headers['Content-Type'] \
               == 'application/x-research-info-systems'

    def get_metadata_response(self):
        # query_url = 'https://www.jstor.org/citation/ris/{id}'.format(
        #     id=self.identifier)
        # verbose_print(f"Fetching from {PColor.PATH(query_url)}")
        # return rq.get(query_url, **cliArg['rqKwargs'])
        return None

    def get_download_url(self, mirror_link):
        assert self.metadata_response is not None
        identifier_override = None
        for line in self.metadata_response.text.splitlines():
            if line.startswith('DO  -'):
                # doc has DOI
                identifier_override = line[6:]
        if identifier_override is None:
            identifier_override = mirror_link \
                                  + 'https://www.jstor.org/stable/' \
                                  + self.identifier
        verbose_print("Calling JSTOR super get_download_url", 3)
        return super(JSTORRepoHandler, self).get_download_url(
            mirror_link,
            # hacky
            identifier_override=identifier_override)
