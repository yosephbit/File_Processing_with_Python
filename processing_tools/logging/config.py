from typing import Literal, Optional, TypedDict

import psutil  # type: ignore
from pythonjsonlogger import jsonlogger  # type: ignore

from processing_tools.types import DocumentMeta, Endpoint


class ServerJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(ServerJsonFormatter, self).add_fields(log_record, record, message_dict)
        # we can add special fields here and then reference them in the
        # format config in logging.conf
        log_record["logger_cls"] = self.__class__.__name__
        log_record["cpu_percent"] = psutil.cpu_percent()
        log_record["memory_available"] = psutil.virtual_memory().available


class FastApiJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(FastApiJsonFormatter, self).add_fields(log_record, record, message_dict)
        # we can add special fields here and then reference them in the
        # format config in logging.conf
        log_record["logger_cls"] = self.__class__.__name__
        log_record["cpu_percent"] = psutil.cpu_percent()
        log_record["memory_available"] = psutil.virtual_memory().available


class DocProcessingLogExtrasBase(TypedDict, total=False):
    log_type: Literal["Document Processing"]
    endpoint: Endpoint


class DocProcessingLogExtras(DocProcessingLogExtrasBase, total=False):
    """
    A pattern for extras to be included in logging calls, such as
    `logger.debug("this is a message", extra=<instance of this>)`

    Optional keys can be declared here. Require ones should go
    in the base class.

    For background see:
    - https://mypy.readthedocs.io/en/latest/more_types.html?highlight=total#mixing-required-and-non-required-items
    - https://github.com/python/mypy/issues/4617
    """

    source_id: Optional[int]
    document_id: Optional[int]
    error_detail: Optional[str]
    size_bytes: int
    file_extension: str
    processing_time: float


def get_doc_processing_log_extra(
    endpoint: Endpoint,
    meta: Optional[DocumentMeta],
) -> DocProcessingLogExtras:
    """
    Get a dict with standardized keys that are suitable for document processing logs.

    Usage:
    ```
    logger.info("this is a message", extra=get_doc_processing_log_extra("od_to_pdf", request.meta))
    ```
    """
    if meta:
        return {
            "source_id": meta["source_id"],
            "document_id": meta["document_id"],
            "log_type": "Document Processing",
            "endpoint": endpoint,
        }
    else:
        return {
            "log_type": "Document Processing",
            "endpoint": endpoint,
        }
