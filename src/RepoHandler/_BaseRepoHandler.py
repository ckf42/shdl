from abc import ABC, abstractmethod
from requests import Response as rq_Response

from typing import Optional, Tuple, Union

from src.CommonUtil import *

if __name__ == '__main__':
    quit()


class _BaseRepoHandler(ABC):
    # properties
    identifier = None
    is_query_valid = None
    metadata = None
    metadata_response = None
    is_meta_response_valid = None

    # init
    def __init__(self, raw_query_str: Optional[str] = None):
        verbose_print("Initiating _Base", 3)
        if raw_query_str is None:
            return
        self.identifier = self.get_identifier(raw_query_str)
        self.is_query_valid = (self.identifier is not None)
        if not self.is_query_valid:
            return
        verbose_print("Fetching metadata response", 3)
        self.metadata_response = self.get_metadata_response()
        verbose_print("Extracting metadata", 3)
        self.metadata = self.extract_metadata()
        self.is_meta_response_valid = self.metadata is not False
        if self.is_meta_response_valid:
            self.metadata.update({
                'id':   self.identifier,
                'repo': self.repo_name
            })

    # abstract properties
    @classmethod
    @property
    @abstractmethod
    def repo_name(cls) -> str:
        """Name of repo"""
        raise NotImplementedError

    @classmethod
    @property
    @abstractmethod
    def query_extract_pattern(cls) -> str:
        """Get the regex pattern in str to clear raw query"""
        raise NotImplementedError

    @classmethod
    @property
    @abstractmethod
    # def mirror_list(cls) -> tuple[str]:
    def mirror_list(cls) -> Tuple[str]:
        # 3.8 compatible type hint
        """
        Get a list of possible mirror URL for file download

        :return: tuple[str]
            A tuple of mirror URL
        """
        raise NotImplementedError

    # abstract class methods
    @classmethod
    @abstractmethod
    def get_identifier(cls, raw_query_str: str) -> Optional[str]:
        """
        Extract the identifier from raw query string,
            assuming the query string is valid

        :param raw_query_str: str.
            The raw query string user inputted
        :return: str
            The identifier
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def _is_meta_query_response_valid(cls, response_obj: rq_Response) -> bool:
        """
        Check if response for metadata is valid

        :param response_obj: requests.Response
            The response to check
        :return: bool.
            Whether the response if valid
        """
        raise NotImplementedError

    # abstract methods
    @abstractmethod
    def get_metadata_response(self) -> rq_Response:
        """
        Get the metadata response and set it to self.metadata_response
        """
        raise NotImplementedError

    @abstractmethod
    def extract_metadata(self) -> Union[bool, dict, None]:
        """
        Get metadata from fetched self.metadata_response

        If able to fetch both author and title from metadata,
        returns a dict with key 'author' and 'title'.
        'author' is a tuple of dict[str, str] with key 'given' and 'family'.

        If able to fetch metadata but unable to parse for author and title,
        returns None.

        Otherwise (if unable to get metadata), return False

        :return: bool (False), None or dict.
        """
        raise NotImplementedError

    @abstractmethod
    def get_download_url(self, mirror_link: str) -> Optional[str]:
        """
        Get file download link

        Returns the direct download link to the file.
        If unable to get the download link, returns None

        :param mirror_link: str.
            The URL of the mirror used to fetch the file
        :return: str, or None.
        """
        raise NotImplementedError
