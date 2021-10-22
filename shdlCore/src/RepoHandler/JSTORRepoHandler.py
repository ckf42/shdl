from re import match as re_match
from re import IGNORECASE

from ..CommonUtil import *
from .DOIRepoHandler import DOIRepoHandler


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
            console_print(f"{PColor.WARNING('Failed')} parsing identifier as "
                          f"type {PColor.INFO(cls.repo_name)}",
                          msg_verbose_level=VerboseLevel.VERBOSE)
            return None

    @classmethod
    def _is_meta_query_response_valid(cls, response_obj):
        console_print("Return status code: " + str(response_obj.status_code),
                      msg_verbose_level=VerboseLevel.DEBUG)
        console_print("Content type: " + response_obj.headers['Content-Type'],
                      msg_verbose_level=VerboseLevel.DEBUG)
        return response_obj.status_code == 200 \
               and response_obj.headers['Content-Type'].startswith(
            'application/x-research-info-systems'
        )

    def get_metadata_response(self):
        # metadata is fetch in self.extract_metadata
        # TODO better resolution
        return None

    def get_download_url(self, mirror_link, **kwargs):
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
        console_print("Calling JSTOR super get_download_url",
                      msg_verbose_level=VerboseLevel.DEBUG)
        return super(JSTORRepoHandler, self).get_download_url(
            mirror_link,
            # hacky
            identifier_override=identifier_override)
