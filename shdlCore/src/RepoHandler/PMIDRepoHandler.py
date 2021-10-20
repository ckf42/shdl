from re import match as re_match
from re import IGNORECASE

from ..CommonUtil import *
from .DOIRepoHandler import DOIRepoHandler


class PMIDRepoHandler(DOIRepoHandler):
    repo_name = "PMID"
    query_extract_pattern \
        = r'^(https?://)?((pubmed|www)\.ncbi\.nlm\.nih\.gov(/pubmed)?|pmid:?)\s*/?(\d+)/?$'
    mirror_list = cliArg['mirror']

    @classmethod
    def get_identifier(cls, raw_query_str):
        match_gp = re_match(cls.query_extract_pattern,
                            raw_query_str,
                            flags=IGNORECASE)
        if match_gp:
            return match_gp.group(5)
        else:
            console_print(f"{PColor.WARNING('Failed')} parsing identifier as "
                          f"type {PColor.INFO(cls.repo_name)}",
                          msg_verbose_level=VerboseLevel.VERBOSE)
            return None

    def get_metadata_response(self):
        console_print(f"{PColor.INFO('Fetching metadata')} "
                      f"for type {PColor.INFO(self.repo_name)}...",
                      msg_verbose_level=VerboseLevel.VERBOSE)
        return rq.get(
            'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?'
            'db=pubmed&id={id}]&retmode=json'.format(id=self.identifier),
            **cliArg['rqKwargs']
        )

    @classmethod
    def _is_meta_query_response_valid(cls, response_obj):
        console_print("Return status code: " + str(response_obj.status_code),
                      msg_verbose_level=VerboseLevel.DEBUG)
        console_print("Content type: " + response_obj.headers['content-type'],
                      msg_verbose_level=VerboseLevel.DEBUG)
        return (response_obj.status_code == 200
                and response_obj.headers['Content-Type'].startswith(
                    'application/json'))

    def extract_metadata(self):
        if not self._is_meta_query_response_valid(self.metadata_response):
            info_print(f"Response is not a valid {self.repo_name} response")
            return False
        json_obj = (lambda x: x[x['uids'][0]])(
            self.metadata_response.json()['result'])
        doc_title = json_obj.get('title', None)
        author_list = list(aDict['name']
                           for aDict in json_obj.get('authors', list())
                           if aDict.get('authtype', '') == 'Author')
        pub_year = json_obj.get('pubdate', '')[:4]
        if doc_title is not None and len(author_list) != 0:
            return {
                'title':  doc_title.strip(' \'".'),
                'author': tuple(dict(zip(('family', 'given'),
                                         aStr.strip().rsplit(' ', 1)))
                                for aStr in author_list),
                'year':   pub_year
            }
        else:
            # even citation record is incomplete
            return None

    def get_download_url(self, mirror_link, **kwargs):
        assert self.metadata_response is not None
        console_print("Calling PMID super get_download_url",
                      msg_verbose_level=VerboseLevel.DEBUG)
        return super(PMIDRepoHandler, self).get_download_url(
            mirror_link,
            # hacky
            init_query_method_override=lambda u, **qkwargs: rq.post(
                u,
                data={'request': self.identifier},
                **qkwargs)
        )
