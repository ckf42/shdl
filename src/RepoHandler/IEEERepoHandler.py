from re import match as re_match
from re import IGNORECASE

from ..CommonUtil import *
from .DOIRepoHandler import DOIRepoHandler


class IEEERepoHandler(DOIRepoHandler):
    repo_name = "IEEE"
    query_extract_pattern \
        = r'^(https?://ieeexplore\.)?ieee(\.org/document/|:|/)?\s*(\d+)$'
    mirror_list = cliArg['mirror']

    @classmethod
    def get_identifier(cls, raw_query_str):
        match_gp = re_match(cls.query_extract_pattern,
                            raw_query_str,
                            flags=IGNORECASE)
        if match_gp:
            return match_gp.group(3)
        else:
            info_print(f"Failed parsing identifier as type {cls.repo_name}")
            return None

    def get_metadata_response(self):
        info_print(f"Fetching metadata for type {self.repo_name}...")
        return rq.get(
            'http://ieeexplore.ieee.org/rest/search/citation/format'
            '?recordIds={id}&download-format=download-ris'
            '&lite=true'.format(id=self.identifier),
            headers={
                'Referer': 'https://ieeexplore.ieee.org/document/{id}'.format(
                    id=self.identifier)}
        )

    @classmethod
    def _is_meta_query_response_valid(cls, response_obj):
        return response_obj.status_code == 200 \
               and response_obj.headers['Content-Length'] != 0

    def extract_metadata(self):
        if not self._is_meta_query_response_valid(self.metadata_response):
            info_print(f"Response is not a valid {self.repo_name} response")
            return False
        doc_title = None
        author_list = list()
        pub_year = ''
        for line in self.metadata_response.json()['data'].splitlines():
            if line.startswith('TI  - '):
                doc_title = line[6:]
            elif line.startswith('AU  - '):
                author_list.append(line[6:])
            elif line.startswith('PY  - '):
                pub_year = line[6:]
        if doc_title is not None and len(author_list) != 0:
            return {
                'title':  doc_title,
                'author': tuple(dict(zip(('given', 'family'),
                                         aStr.strip().rsplit(' ', 1)))
                                for aStr in author_list),
                'year':   pub_year
            }
        else:
            # even citation record is incomplete
            return None

    def get_download_url(self, mirror_link, **kwargs):
        assert self.metadata_response is not None
        identifier_override = None
        for line in self.metadata_response.json()['data'].splitlines():
            if line.startswith('DO  - '):
                # doc has DOI
                self.identifier = line[6:]
                info_print(f"Document has DOI {self.identifier}. "
                           "Will use this for querying mirror")

                identifier_override = self.identifier
                break
        if identifier_override is None:
            identifier_override = (
                    mirror_link
                    + 'https://ieeexplore.ieee.org/document/'
                    + self.identifier)

        console_print("Calling JSTOR super get_download_url",
                      msg_verbose_level=VerboseLevel.DEBUG)
        return super(IEEERepoHandler, self).get_download_url(
            mirror_link,
            # hacky
            identifier_override=identifier_override)
