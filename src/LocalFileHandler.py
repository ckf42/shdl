from io import BufferedWriter

import requests as rq
from pathlib import Path
from typing import Union

from src.CommonUtil import *
from src.CLIArgParser import *

if __name__ == '__main__':
    quit()


def _get_local_file_write_handler(
        write_path_obj: Path) -> Union[BufferedWriter, bool]:
    if len(str(write_path_obj)) >= 250:
        info_print(PColor.ERROR("ERROR:"), end=" ")
        info_print("Target download path is too long")
        return False
    if cliArg['dryrun']:
        info_print("Dryrun. Skipping getting local file handle")
        return True
    info_print(f"Downloading to {PColor.PATH(str(write_path_obj))}")
    try:
        f_handle = write_path_obj.open('wb')
    except (PermissionError, FileNotFoundError):
        # TODO better handling of exceptions
        info_print(PColor.ERROR("ERROR:"), end=" ")
        info_print("Cannot write to "
                   f"target path \"{PColor.PATH(str(write_path_obj))}\"")
        return False
    return f_handle


def _download_file_to_local(target_url: str,
                            local_file_handle: BufferedWriter,
                            **kwargs) -> bool:
    if cliArg['dryrun']:
        # just to be safe
        assert local_file_handle.closed
        info_print("Dryrun. Skipping download")
        return True
    downloaded_size = 0
    last_line_len = 0
    dl_msg = None
    info_print(f"Downloading from {PColor.PATH(target_url)} ...")
    with rq.get(target_url, stream=True, **kwargs) as dl_res:
        file_size = dl_res.headers.get('Content-Length', None)
        if file_size is None:
            info_print("File size not known")
        else:
            file_size = int(file_size)
            info_print("File size: " + human_byte_unit_string(file_size))
        with local_file_handle:
            for data_chunk in dl_res.iter_content(chunk_size=cliArg['chunk']):
                local_file_handle.write(data_chunk)
                downloaded_size += len(data_chunk)
                if file_size is None:
                    dl_msg = "Downloaded " \
                             + human_byte_unit_string(downloaded_size)
                else:
                    dl_msg = "Download " \
                             f"{downloaded_size / file_size * 100 :.2f}% " \
                             f"({human_byte_unit_string(downloaded_size)})"
                info_print(dl_msg, end="")
                len_dl_msg = len(dl_msg)
                info_print(" " * (last_line_len - len_dl_msg), end="\r")
                last_line_len = len_dl_msg
    info_print("\nDownload done")
    return True


def fetch_url_to_local_path(target_url: str,
                            target_local_path_obj: Path,
                            **kwargs) -> bool:
    file_handle = _get_local_file_write_handler(target_local_path_obj)
    if isinstance(file_handle, bool):
        return file_handle
    dl_success_status = _download_file_to_local(target_url,
                                                file_handle,
                                                **kwargs)
    if cliArg['piping'] and dl_success_status:
        info_print(str(target_local_path_obj.resolve(True)),
                   print_suppress=False)
    return dl_success_status
