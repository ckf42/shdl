from re import match as re_match
from re import IGNORECASE

from ..CommonUtil import *
from .DOIRepoHandler import DOIRepoHandler


class SciDirRepoHandler(DOIRepoHandler):
    repo_name = "ScienceDirect"
    query_extract_pattern \
        = r'^(https?://)?(www\.)?sci(ence)?dir(ect)?' \
          r'(\.com/science/article/|:|/)\s*((.+?/)?\s*.+)$'
    mirror_list = cliArg['mirror']

    doc_type = None

    @classmethod
    def get_identifier(cls, raw_query_str):
        match_gp = re_match(cls.query_extract_pattern,
                            raw_query_str,
                            flags=IGNORECASE)
        if match_gp:
            return match_gp.group(6)
        else:
            info_print(f"{PColor.WARNING('Failed')} parsing identifier as "
                       f"type {PColor.INFO(cls.repo_name)}")
            return None

    def get_metadata_response(self):
        console_print(f"{PColor.INFO('Fetching metadata')} "
                      f"for type {PColor.INFO(self.repo_name)}...",
                      msg_verbose_level=VerboseLevel.VERBOSE)
        splitted_id = self.identifier.split('/', 1)
        if len(splitted_id) == 1:
            info_print(PColor.WARNING("WARNING:"), end=" ")
            info_print("Cannot decide identifier type. "
                       "Assuming it is PII")
            self.doc_type, self.identifier = 'pii', self.identifier
        else:
            self.doc_type, self.identifier = splitted_id
        console_print(f"Discovered identifier type: {self.doc_type}",
                      msg_verbose_level=VerboseLevel.VERBOSE)
        return rq.get(
            'https://www.sciencedirect.com/sdfe/arp/cite?'
            '{type}={id}'
            '&format=application%2Fx-research-info-systems'
            '&withabstract=false'.format(id=self.identifier,
                                         type=self.doc_type),
            **cliArg['rqKwargs']
        )

    @classmethod
    def _is_meta_query_response_valid(cls, response_obj):
        return response_obj.status_code == 200 \
               and response_obj.headers['content-type'].startswith(
            'application/x-research-info-systems')

    def extract_metadata(self):
        if not self._is_meta_query_response_valid(self.metadata_response):
            console_print(f"Response is not a valid {self.repo_name} response",
                          msg_verbose_level=VerboseLevel.INFO)
            return False
        doc_title = None
        author_list = list()
        pub_year = ''
        for line in self.metadata_response.text.splitlines():
            if line.startswith('T1  - '):
                doc_title = line[6:]
            elif line.startswith('AU  - '):
                author_list.append(line[6:])
            elif line.startswith('PY  - '):
                pub_year = line[6:]
        if doc_title is not None and len(author_list) != 0:
            return {
                'title':  doc_title,
                'author': tuple(dict(zip(('family', 'given'),
                                         aStr.strip().rsplit(', ', 1)))
                                for aStr in author_list),
                'year':   pub_year
            }
        else:
            # even citation record is incomplete
            return None

    def get_download_url(self, mirror_link, **kwargs):
        assert self.metadata_response is not None
        identifier_override = None
        for line in self.metadata_response.text.splitlines():
            if line.startswith('DO  - '):
                # doc has DOI
                self.identifier = re_match(r'^DO {2}- .+?doi.+?/(.+)$',
                                           line).group(1)
                info_print(f"Document has DOI {self.identifier}. "
                           "Will use this for querying mirror")
                identifier_override = self.identifier
                break
            elif identifier_override is not None and line.startswith('UR  - '):
                identifier_override = line[6:]
                # keep looking for DOI
        if identifier_override is None:
            identifier_override = (
                    mirror_link
                    + 'https://www.sciencedirect.com/science/article/'
                    + f'{self.doc_type}/'
                    + self.identifier)

        console_print("Calling SciDir super get_download_url",
                      msg_verbose_level=VerboseLevel.DEBUG)
        return super(SciDirRepoHandler, self).get_download_url(
            mirror_link,
            # hacky
            identifier_override=identifier_override)
