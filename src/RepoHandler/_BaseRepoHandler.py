from abc import ABC, abstractmethod
from requests import Response as rq_Response

from typing import Optional, Union

if __name__ == '__main__':
    quit()


class _BaseRepoHandler(ABC):
    # properties
    identifier = None
    is_query_valid = None
    meta_response = None
    is_meta_response_valid = None

    # init
    def __init__(self, raw_query_str: str) -> None:
        self.identifier = self.get_identifier(raw_query_str)
        self.is_query_valid = (self.identifier is not None)
        if not self.is_query_valid:
            return
        self.meta_response = self.get_metadata()
        self.is_meta_response_valid = (self.meta_response is dict)

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
    def mirror_list(cls) -> tuple[str]:
        """
        Get a list of possible mirror URL for file download

        :return: tuple[str]
            A tuple of mirror URL
        """
        raise NotImplementedError

    # abstract classmethods
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
    def is_meta_query_response_valid(cls, response_obj: rq_Response) -> bool:
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
    def get_metadata(self) -> Union[bool, dict, None]:
        """
        Get metadata from identifier

        If able to fetch both author and title from metadata,
        returns a dict with key 'author' and 'title'.
        'author' is a tuple of dict[str] with key 'given' and 'family'.

        If able to fetch metadata but unable to parse for author and title,
        returns None.

        Otherwise (if unable to get metadata), return False

        :return: bool (False), None or dict.
        """
        raise NotImplementedError

    @abstractmethod
    def get_download_url(self,
                         mirror_link: str,
                         **kwargs) -> Optional[str]:
        """
        Get file download link

        Returns the direct download link to the file.
        If unable to get the download link, returns None

        :param mirror_link: str.
            The URL of the mirror used to fetch the file
        :param kwargs:
            Additional parameter used for network requests
        :return: str, or None.
        """
        raise NotImplementedError
