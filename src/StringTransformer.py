from html import unescape
from re import split, sub
from unicodedata import category, name, normalize

from typing import Dict, Tuple

if __name__ == '__main__':
    quit()


def sanitize_filename(proposed_filename: str) -> str:
    """
    Transform a string to a valid filename

    :param proposed_filename: str
        The filename string to be transformed
    :return: str.
        The sanitized filename string
    """
    return ' '.join(
        normalize(
            'NFKD',
            proposed_filename.translate(str.maketrans(
                {k: ' ' for k in '/<>:\"\\|?*'}
            )).translate(str.maketrans({
                '’': '\''
            }))
            # unicode non Sm category replacement
        ).encode('ASCII', 'ignore').decode().split(None)
    )


# def transform_to_author_str(author_dict_tuple: tuple[dict[str, str]]) -> str:
def transform_to_author_str(author_dict_tuple: Tuple[Dict[str, str]]) -> str:
    # 3.8 compatible type hint
    """
    Transform a tuple of author information into a single formatted string

    :param author_dict_tuple: tuple[dict[str, str]]
        A tuple of author information.
        Each dict assumed to have key 'given' and 'family' with string value
    :return: str.
        A single formatted string
    """
    return ', '.join(
        ''.join(
            (gNamePart
             if len(gNamePart) <= 1 or not gNamePart.isalpha()
             else (gNamePart[0] + '.'))
            for gNamePart
            in split(r'\b', author_name_dict['given'])
        )
        + ' '
        + author_name_dict['family'].strip()
        for author_name_dict in author_dict_tuple)


def convert_math_symbol_to_name(raw_title_string: str) -> str:
    """
    Sanitize a Unicode string with math symbols

    :param raw_title_string: str.
        The input string to be sanitized (usually the title of a document)
    :return: str.
        The sanitized string with math symbols converted into their names
    """
    return ''.join((f' {name(c).title()}'
                    if not c.isascii() and category(c) == 'Sm'
                    else c)
                   for c
                   in sub('</?.+?>', '', unescape(raw_title_string)))


# list modified from https://gist.github.com/sebleier/554280
_stopword_list = (
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an',
    'and', 'any', 'are', 'as', 'at', 'be', 'because', 'been', 'before',
    'being', 'below', 'between', 'both', 'but', 'by', 'can', 'did', 'do',
    'does', 'doing', 'don', 'down', 'during', 'each', 'few', 'for', 'from',
    'further', 'had', 'has', 'have', 'having', 'here', 'how', 'if', 'in',
    'into', 'is', 'just', 'more', 'most', 'no', 'nor', 'not', 'now', 'of',
    'off', 'on', 'once', 'only', 'or', 'other', 'out', 'over', 'own', 's',
    'same', 'should', 'so', 'some', 'such', 't', 'than', 'that', 'the',
    'then', 'there', 'these', 'this', 'those', 'through', 'to', 'too',
    'under', 'until', 'up', 'very', 'was', 'were', 'what', 'when', 'where',
    'which', 'while', 'who', 'whom', 'why', 'will', 'with',
)


# TODO better method?
def transform_to_title(raw_title_str: str) -> str:
    """
    Convert a string into title casing

    :param raw_title_str: str
        The title string to be converted
    :return: str.
        The converted string in title casing
    """
    word_list = split(r'([ \-])\b', raw_title_str)
    if len(word_list) <= 1:
        return raw_title_str
    else:
        return (word_list[0]
                if word_list[0].isupper()
                else word_list[0].capitalize()) \
               + ''.join(
            map(lambda w: w.lower() \
                if w.lower() in _stopword_list \
                else (w if w.isupper() else w.capitalize()),
                word_list[1:]))
