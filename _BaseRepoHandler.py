from abc import ABC, abstractmethod
from re import IGNORECASE
from re import match as re_match


class _BaseRepoHandler(ABC):
    @classmethod
    @abstractmethod
    def get_repo_name(cls):
        pass

    @classmethod
    @abstractmethod
    def get_query_sanitizer_string(cls):
        return

    @classmethod
    @abstractmethod
    def fetch_metadata(cls, identifier_str):
        pass

    @classmethod
    @abstractmethod
    def is_meta_query_response_valid(cls, response_obj):
        pass

    @classmethod
    @abstractmethod
    def get_download_url(cls, identifier_str, mirror_link, **kwargs):
        pass

    @classmethod
    def is_query_valid(cls, query_str):
        return re_match(cls.get_query_sanitizer_string(),
                        query_str,
                        IGNORECASE) is not None