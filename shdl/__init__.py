from shdl.src import *


def main():
    console_print("Received cli arguments: ",
                  msg_verbose_level=VerboseLevel.DEBUG)
    for _k, _v in cliArg.items():
        console_print(PColor.INFO(_k) + ": " + str(_v),
                      msg_verbose_level=VerboseLevel.DEBUG)

    # check repo
    repo_obj = next((obj
                     for cls in registered_repo_list
                     if (obj := cls(cliArg['identifier'])).is_query_valid),
                    None)
    if repo_obj is None:
        info_print(PColor.WARNING("WARNING:"), end=" ")
        info_print("Input query format not recognized. "
                   "Assuming it is sanitized DOI")
        repo_obj = DOIRepoHandler('doi: ' + cliArg['identifier'])
    info_print(f"Detected identifier type: {PColor.INFO(repo_obj.repo_name)}")
    info_print(f"Sanitized identifier: {PColor.PATH(repo_obj.identifier)}")

    # check metadata
    console_print("Metadata response: ", msg_verbose_level=VerboseLevel.DEBUG)
    if not repo_obj.is_meta_response_valid:
        quit_with_error(ErrorType.QUERY_INVALID,
                        error_msg="No metadata found")
    for _k, _v in repo_obj.metadata.items():
        console_print(PColor.INFO(_k) + ": " + str(_v))

    # patch autoname
    proposedName = cliArg['output']
    if proposedName is None and cliArg['autoname']:
        if repo_obj.metadata is None:
            info_print(PColor.WARNING("WARNING:"), end=" ")
            info_print("Unable to fetch metadata "
                       f"for identifier {repo_obj.identifier}")
            info_print("Name falls back to remote name")
            cliArg['autoname'] = False  # not really necessary
        else:
            assert isinstance(repo_obj.metadata, dict)
            assert 'title' in repo_obj.metadata
            assert 'author' in repo_obj.metadata
            console_print(f"{PColor.INFO('Proposed format')}: "
                          f"{cliArg['autoformat']}",
                          msg_verbose_level=VerboseLevel.VERBOSE)
            try:
                proposedName = autoname_patcher(repo_obj.metadata,
                                                cliArg['autoformat'])
            except ValueError:
                info_print(PColor.ERROR("ERROR:"), end=" ")
                info_print("Autoformat invalid. "
                           "Name falls back to remote name")
            except KeyError as e:
                info_print(PColor.ERROR("ERROR:"), end=" ")
                info_print(f"Unknown keyword: {e.args[0]}")
                info_print("Autoformat invalid. "
                           "Name falls back to remote name")
            else:
                # check validity later when dl link is fetched
                # as ext is yet not known
                console_print("Proposed name: " + PColor.PATH(proposedName),
                              msg_verbose_level=VerboseLevel.VERBOSE)

    # get download link
    if len(repo_obj.mirror_list) == 0:
        quit_with_error(
            ErrorType.ARG_INVALID,
            error_msg="No known mirror. "
                      "Please specify mirrors with --mirror switch"
        )
    assert len(repo_obj.mirror_list) != 0
    dlURL = next((lnk
                  for mirrorURL in repo_obj.mirror_list
                  if
                  (lnk := repo_obj.get_download_url(mirrorURL)) is not None),
                 None)
    if dlURL is None:
        quit_with_error(ErrorType.FILE_NOT_FOUND)
    console_print("Download link: " + PColor.PATH(dlURL),
                  msg_verbose_level=VerboseLevel.VERBOSE)

    # download
    if proposedName is None:
        proposedName = dlURL.rsplit('/', 1)[-1].rsplit('.', 1)[0]
    downloadPath = cliArg['dir'] / (
            proposedName + '.' + dlURL.rsplit('.', 1)[-1])
    console_print("Download path: " + PColor.PATH(str(downloadPath)),
                  msg_verbose_level=VerboseLevel.VERBOSE)
    if not fetch_url_to_local_path(dlURL, downloadPath):
        quit_with_error(ErrorType.OUTPUT_ERROR,
                        error_msg="Cannot write to "
                                  + PColor.PATH(str(downloadPath)))


console_print(PColor.INFO("Setup done"),
              msg_verbose_level=VerboseLevel.INFO)
