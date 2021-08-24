from abc import ABC, abstractmethod
from requests import Response as rq_Response
from re import match as re_match
from re import IGNORECASE

from typing import Optional, Union

if __name__ == '__main__':
    quit()


class _BaseRepoHandler(ABC):
    @classmethod
    @abstractmethod
    def get_repo_name(cls) -> str:
        """Name of repo"""
        pass

    @classmethod
    @abstractmethod
    def get_query_extract_pattern(cls) -> str:
        """Get the regex pattern in str to clean raw query"""
        pass

    @classmethod
    @abstractmethod
    def get_metadata(cls, identifier_str: str) -> Union[bool, dict, None]:
        """
        Get metadata from identifier

        :param identifier_str: str
            The target identifier
        :return: bool (False), None or dict.
        If able to fetch both author and title from metadata,
            returns a dict with key 'author' and 'title'.
            'author' is a tuple of dict[str] with key 'given' and 'family'.
        If able to fetch metadata but unable to parse for author and title,
            returns None.
        Otherwise (if unable to get metadata), return False
        """
        pass

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
        pass

    @classmethod
    @abstractmethod
    def get_download_url(cls,
                         identifier_str: str,
                         mirror_link: str,
                         **kwargs) -> Optional[str]:
        """
        Get file download link

        :param identifier_str: str.
            The identifier of the target file
        :param mirror_link: str.
            The URL of the mirror used to fetch the file
        :param kwargs:
            Additional parameter used for network requests
        :return: str, or None.
            The direct download link to the file.
            If unable to get the download link, returns None
        """
        pass

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
        pass

    @classmethod
    def is_query_valid(cls, raw_query_str: str) -> bool:
        """
        Check if the raw query string is recognized

        :param raw_query_str: str.
            The raw query string user inputted
        :return: bool
            Whether the string is in a recognized format
        """
        return cls.get_identifier(raw_query_str) is not None

    @classmethod
    @abstractmethod
    def get_mirror_list(cls) -> tuple[str]:
        """
        Get a list of possible mirror URL for file download

        :return: tuple[str]
            A tuple of mirror URL
        """
        pass
