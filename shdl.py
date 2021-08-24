#!/usr/bin/env python3

from src.CommonUtil import *
from src.StringTransformer import *
from src.LocalFileHandler import *
from src.RepoHandler.RegisteredRepo import registered_repo_list

if __name__ != '__main__':
    quit()

verbose_print(cliArg, msg_verbose_level=2)

# check repo
query_type_cls = next((cls
                       for cls in registered_repo_list
                       if cls.is_query_valid(cliArg.doi)), None)
if query_type_cls is None:
    error_reporter.quit_now(ErrorType.QUERY_INVALID,
                            error_msg="Input query is not recognized")
else:
    verbose_print(
        f"Detected identifier type: {query_type_cls.get_repo_name()}")

# extract id
identifier_str = query_type_cls.get_identifier(cliArg.doi)
verbose_print(f"Sanitized identifier: {identifier_str}")
metadata_res = query_type_cls.get_metadata(identifier_str)
if metadata_res is False:
    error_reporter.quit_now(
        ErrorType.QUERY_INVALID,
        error_msg=f"No metadata for identifier {identifier_str}"
    )
verbose_print(str(metadata_res), msg_verbose_level=2)

# check autoname
proposedName = cliArg.output
if proposedName is None and cliArg.autoname:
    if metadata_res is None:
        info_print(PColor.WARNING("WARNING:"), end=" ")
        info_print(f"Unable to fetch metadata for identifier {identifier_str}")
        info_print("Fallback to remote name")
        cliArg.autoname = False  # not really necessary
    else:
        proposedTitle = transform_to_title(
            convert_math_symbol_to_name(metadata_res['title']))
        proposedAuthorStr = transform_to_author_str(metadata_res['author'])
        proposedName = sanitize_filename(f"[{proposedAuthorStr}]"
                                         + proposedTitle)
        # check validity later when dl link is fetched as ext is yet not known
verbose_print(proposedName, 2)

# get download link
dlURL = next((lnk
              for mirrorURL in query_type_cls.get_mirror_list()
              if (lnk := query_type_cls
                  .get_download_url(identifier_str,
                                    mirrorURL)) is not None),
             None)
if dlURL is None:
    error_reporter.quit_now(ErrorType.FILE_NOT_FOUND)
verbose_print(dlURL, 2)

# ready download
if proposedName is None:
    proposedName = dlURL.rsplit('/', 1)[-1]
else:
    proposedName += '.' + dlURL.rsplit('.', 1)[-1]
downloadPath = cliArg.dir / proposedName
verbose_print(PColor.PATH(str(downloadPath)), 2)
if not fetch_url_to_local_path(dlURL, downloadPath):
    error_reporter.quit_now(ErrorType.OUTPUT_ERROR,
                            msg="Cannot write to " \
                                + PColor.PATH(str(downloadPath)))
