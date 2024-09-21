from pathlib import Path
from typing import Literal, Optional, TypedDict

from pydantic import AnyHttpUrl


class DocumentMeta(TypedDict):
    source_id: Optional[int]
    document_id: Optional[int]


class FileConverter:
    def __init__(self, meta: Optional[DocumentMeta]):
        self.meta = meta

    def convert(self, path: Path):
        raise NotImplementedError("Subclasses must implement this")


class UrlConverter:
    def __init__(self, meta: Optional[DocumentMeta]):
        self.meta = meta

    def convert(self, url: AnyHttpUrl):
        raise NotImplementedError("Subclasses must implement this")


Endpoint = Literal["od_to_pdf", "html_to_pdf", "xls_to_xlsx"]
OD_TO_PDF_ENDPOINT: Endpoint = "od_to_pdf"
HTML_TO_PDF_ENDPOINT: Endpoint = "html_to_pdf"
XLS_TO_XLSX_ENDPOINT: Endpoint = "xls_to_xlsx"
