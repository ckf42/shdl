#!/usr/bin/env python3

from src.CLIArgParser import *
from src.CommonUtil import *
from src.StringTransformer import *
from src.LocalFileHandler import *
from src.RepoHandler.RegisteredRepo import *

if __name__ != '__main__':
    quit()

verbose_print(cliArg, msg_verbose_level=2)

# check repo
repo_obj = next((obj
                 for cls in registered_repo_list
                 if (obj := cls(cliArg.identifier)).is_query_valid),
                None)
if repo_obj is None:
    # error_reporter.quit_now(ErrorType.QUERY_INVALID,
    #                         error_msg="Input query is not recognized")
    info_print(PColor.WARNING("WARNING:"), end=" ")
    info_print("Input query format not recognized. "
               "Assuming it is sanitized DOI")
    repo_obj = DOIRepoHandler('doi: ' + cliArg.identifier)
verbose_print(f"Detected identifier type: {repo_obj.repo_name}")
verbose_print(f"Sanitized identifier: {repo_obj.identifier}")

# check metadata
verbose_print("Metadata response: " + str(repo_obj.metadata), 2)
if not repo_obj.is_meta_response_valid:
    error_reporter.quit_now(ErrorType.QUERY_INVALID,
                            error_msg="No metadata found")

# patch autoname
proposedName = cliArg.output
if proposedName is None and cliArg.autoname:
    if repo_obj.metadata is None:
        info_print(PColor.WARNING("WARNING:"), end=" ")
        info_print("Unable to fetch metadata "
                   f"for identifier {repo_obj.identifier}")
        info_print("Name falls back to remote name")
        cliArg.autoname = False  # not really necessary
    else:
        assert isinstance(repo_obj.metadata, dict)
        assert 'title' in repo_obj.metadata
        assert 'author' in repo_obj.metadata
        author_tuple = repo_obj.metadata['author']
        title_kw_dict = {
            'repo':         repo_obj.repo_name.lower(),
            'authors':      transform_to_author_str(author_tuple),
            'authorEtAl':   transform_to_author_str(author_tuple[:3])
                            + (', et al.' if len(author_tuple) > 3 else ''),
            'authorFamily': ', '.join(aDict['family']
                                      for aDict in author_tuple),
            'title':        transform_to_title(convert_math_symbol_to_name(
                repo_obj.metadata['title'])),
            'identifier':   repo_obj.identifier.replace('/', '@'),
            'year':         repo_obj.metadata['year'],
            'year2':        repo_obj.metadata['year'][-2:],
        }
        try:
            proposedName = sanitize_filename(
                cliArg.autoformat.format_map(title_kw_dict))
        except ValueError:
            info_print(PColor.ERROR("ERROR:"), end=" ")
            info_print("Autoformat invalid. "
                       "Name falls back to remote name")
        else:
            # check validity later when dl link is fetched
            # as ext is yet not known
            verbose_print("Proposed name: " + PColor.PATH(proposedName), 2)

# get download link
dlURL = next((lnk
              for mirrorURL in repo_obj.mirror_list
              if (lnk := repo_obj.get_download_url(mirrorURL)) is not None),
             None)
if dlURL is None:
    error_reporter.quit_now(ErrorType.FILE_NOT_FOUND)
verbose_print("Download link: " + PColor.PATH(dlURL), 2)

# download
if proposedName is None:
    proposedName = dlURL.rsplit('/', 1)[-1].rsplit('.', 1)[0]
downloadPath = cliArg.dir / (proposedName + '.' + dlURL.rsplit('.', 1)[-1])
verbose_print("Download path: " + PColor.PATH(str(downloadPath)), 2)
if not fetch_url_to_local_path(dlURL, downloadPath):
    error_reporter.quit_now(ErrorType.OUTPUT_ERROR,
                            error_msg="Cannot write to "
                                      + PColor.PATH(str(downloadPath)))