import os

import requests

from processing_tools.settings import settings


def download_local_file(url, file_path):
    input_file_response = requests.get(url, allow_redirects=True)
    with open(file_path, "wb") as f:
        for chunk in input_file_response.iter_content(
            chunk_size=settings.iter_chunk_size
        ):
            f.write(chunk)


def filename_to_pdf_name(filename: str) -> str:
    return f"{os.path.splitext(filename)[0]}.pdf"


def get_extension(path: str) -> str:
    """
    Get the extension of a file, lowercased.

    NOTE: we do not include a leading "."

    >>> get_extension("this is my file.pdf")
    'pdf'

    >>> get_extension("this is my file")
    ''

    >>> get_extension("/home/user/Desktop/this is my file.MBOX")
    'mbox'
    """
    return os.path.splitext(path)[1].strip().lower()[1:]
