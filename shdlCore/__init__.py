from shdlCore.src import *


def main():
    # check repo
    repo_obj = next((obj
                     for cls in registered_repo_list
                     if (obj := cls(cliArg['identifier'])).is_query_valid),
                    None)
    if repo_obj is None:
        console_print(PColor.WARNING("WARNING:"), end=" ")
        console_print("Input query format not recognized. "
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
        console_print(PColor.INFO(_k) + ": " + str(_v),
                      msg_verbose_level=VerboseLevel.DEBUG)

    # patch autoname
    proposed_name = cliArg['output']
    if proposed_name is None and cliArg['autoname']:
        if repo_obj.metadata is None:
            console_print(PColor.WARNING("WARNING:"), end=" ")
            console_print("Unable to fetch metadata "
                          f"for identifier {repo_obj.identifier}")
            console_print("Name falls back to remote name")
            cliArg['autoname'] = False  # not really necessary
        else:
            assert isinstance(repo_obj.metadata, dict)
            assert 'title' in repo_obj.metadata
            assert 'author' in repo_obj.metadata
            console_print(f"{PColor.INFO('Proposed format')}: "
                          f"{cliArg['autoformat']}",
                          msg_verbose_level=VerboseLevel.VERBOSE)
            try:
                proposed_name = autoname_patcher(repo_obj.metadata,
                                                 cliArg['autoformat'])
            except ValueError:
                console_print(PColor.ERROR("ERROR:"), end=" ")
                console_print("Autoformat invalid. "
                              "Name falls back to remote name")
            except KeyError as e:
                console_print(PColor.ERROR("ERROR:"), end=" ")
                console_print(f"Unknown keyword: {e.args[0]}")
                console_print("Autoformat invalid. "
                              "Name falls back to remote name")
            else:
                # check validity later when dl link is fetched
                # as ext is yet not known
                console_print("Proposed name: " + PColor.PATH(proposed_name),
                              msg_verbose_level=VerboseLevel.VERBOSE)

    # get download link
    if len(repo_obj.mirror_list) == 0:
        quit_with_error(
            ErrorType.ARG_INVALID,
            error_msg="No known mirror. "
                      "Please specify mirrors with --mirror switch"
        )
    assert len(repo_obj.mirror_list) != 0
    dl_url = next(
        (lnk
         for mirrorURL in repo_obj.mirror_list
         if (lnk := repo_obj.get_download_url(mirrorURL)) is not None),
        None
    )
    if dl_url is None:
        quit_with_error(ErrorType.FILE_NOT_FOUND)
    console_print("Download link: " + PColor.PATH(dl_url),
                  msg_verbose_level=VerboseLevel.VERBOSE)

    # download
    if proposed_name is None:
        proposed_name = dl_url.rsplit('/', 1)[-1].rsplit('.', 1)[0]
    download_path = cliArg['dir'] / (
            proposed_name + '.' + dl_url.rsplit('.', 1)[-1])
    console_print("Download path: " + PColor.PATH(str(download_path)),
                  msg_verbose_level=VerboseLevel.VERBOSE)
    if not fetch_url_to_local_path(dl_url, download_path):
        quit_with_error(ErrorType.OUTPUT_ERROR,
                        error_msg="Failed to download file ")


console_print(PColor.INFO("Setup done"),
              msg_verbose_level=VerboseLevel.INFO)
