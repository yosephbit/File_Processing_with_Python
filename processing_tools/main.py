import logging
import logging.config
import os
import tempfile
import time
from pathlib import Path
from typing import Literal, Optional, Union

import sentry_sdk
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse, Response
from prometheus_fastapi_instrumentator import Instrumentator  # type: ignore
from pydantic import AnyHttpUrl, BaseModel
from rich.logging import RichHandler
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from processing_tools.html import html_to_pdf_browserless, html_to_pdf_wkhtmltopdf
from processing_tools.logging.config import get_doc_processing_log_extra
from processing_tools.office import OfficeDocumentConverter
from processing_tools.settings import settings
from processing_tools.spreadsheet import XLSToXLSXConverter
from processing_tools.types import (
    HTML_TO_PDF_ENDPOINT,
    OD_TO_PDF_ENDPOINT,
    XLS_TO_XLSX_ENDPOINT,
    DocumentMeta,
)
from processing_tools.utils import download_local_file, get_extension

if not settings.debug:
    logging.config.fileConfig("processing_tools/logging/logging.conf")
    logger = logging.getLogger(__name__)
else:
    logging.basicConfig(
        level="NOTSET",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    logger = logging.getLogger()
    logger.debug(
        "[bold red underline italic]Processing Tools is in debug mode: DO NOT ALLOW IN PRODUCTION[/]",
        extra={"markup": True},
    )


app = FastAPI(
    debug=settings.debug,
    openapi_url="/openapi.json" if settings.debug else "",
    title="Processing Tools",
    description="A collection of tools for processing files, coverting to PDF, and other tasks.",
    version="0.1.0",
)
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=False,
    should_group_untemplated=False,
    should_instrument_requests_inprogress=True,
    excluded_handlers=[".*admin.*", "/metrics"],
    inprogress_labels=True,
)
instrumentator.instrument(app)
instrumentator.expose(app, should_gzip=True)


########################
# Sentry Configuration #
########################
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=settings.sentry_release,
        traces_sample_rate=settings.sentry_sample_rate,
    )
    app.add_middleware(SentryAsgiMiddleware)


class ConversionRequest(BaseModel):
    url: AnyHttpUrl
    meta: Optional[DocumentMeta]
    engine: Union[Literal["browserless"], Literal["wkhtmltopdf"]]


class ConversionURLOnlyRequest(BaseModel):
    url: AnyHttpUrl
    meta: Optional[DocumentMeta]


@app.post("/xls_to_xlsx/", tags=["XLSToXLSX"])
async def xls_to_xlsx(request: ConversionURLOnlyRequest) -> Response:
    t_start = time.time()
    logger.info(
        "xls_to_xlsx starting 🏎",
        extra=get_doc_processing_log_extra(XLS_TO_XLSX_ENDPOINT, request.meta),
    )
    try:

        with tempfile.TemporaryDirectory() as tmp_dir:

            extension = get_extension(request.url.path or "")
            in_path = Path(os.path.join(tmp_dir, f"file.{extension}"))
            out_path = Path(os.path.join(tmp_dir, "file.xlsx"))

            download_local_file(request.url, in_path)

            extra = get_doc_processing_log_extra(XLS_TO_XLSX_ENDPOINT, request.meta)
            extra["file_extension"] = extension
            extra["size_bytes"] = os.path.getsize(in_path)

            logger.debug(
                "xls_to_xlsx downloaded file",
                extra=extra,
            )

            converter = XLSToXLSXConverter(request.meta)
            converted_bytes = await converter.convert(in_path)

            t_total = time.time() - t_start

            extra = get_doc_processing_log_extra(XLS_TO_XLSX_ENDPOINT, request.meta)
            extra["file_extension"] = extension
            extra["size_bytes"] = os.path.getsize(in_path)
            extra["processing_time"] = t_total
            logger.info(
                "xls_to_xlsx finished 🏁",
                extra=extra,
            )

            headers = {
                "Content-Disposition": f"attachment; filename={os.path.basename(out_path)}"
            }
            return Response(
                content=converted_bytes, media_type="application/xlsx", headers=headers
            )

    except Exception:
        logger.exception(
            "xls_to_xlsx errored 🪵",
            extra=get_doc_processing_log_extra(XLS_TO_XLSX_ENDPOINT, request.meta),
        )
        return Response("Could not convert file to xlsx", status_code=500)


@app.post("/od_to_pdf/", tags=["OpenDocToPDF"])
async def od_to_pdf(request: ConversionURLOnlyRequest) -> Response:
    t_start = time.time()
    logger.info(
        "od_to_pdf starting 🏎",
        extra=get_doc_processing_log_extra(OD_TO_PDF_ENDPOINT, request.meta),
    )
    try:

        with tempfile.TemporaryDirectory() as tmp_dir:

            extension = get_extension(request.url.path or "")
            in_path = Path(os.path.join(tmp_dir, f"file.{extension}"))
            out_path = Path(os.path.join(tmp_dir, "file.pdf"))

            download_local_file(request.url, in_path)

            extra = get_doc_processing_log_extra(OD_TO_PDF_ENDPOINT, request.meta)
            extra["file_extension"] = extension
            extra["size_bytes"] = os.path.getsize(in_path)

            logger.debug(
                "od_to_pdf downloaded file",
                extra=extra,
            )

            converter = OfficeDocumentConverter(request.meta)
            converted_bytes = await converter.convert(in_path)

            t_total = time.time() - t_start

            extra = get_doc_processing_log_extra(OD_TO_PDF_ENDPOINT, request.meta)
            extra["file_extension"] = extension
            extra["size_bytes"] = os.path.getsize(in_path)
            extra["processing_time"] = t_total
            logger.info(
                "od_to_pdf finished 🏁",
                extra=extra,
            )

            headers = {
                "Content-Disposition": f"attachment; filename={os.path.basename(out_path)}"
            }
            return Response(
                content=converted_bytes, media_type="application/pdf", headers=headers
            )

    except Exception:
        logger.exception(
            "od_to_pdf errored 🪵",
            extra=get_doc_processing_log_extra(OD_TO_PDF_ENDPOINT, request.meta),
        )
        return Response("Could not convert file to pdf", status_code=500)


@app.post("/html_to_pdf/")
async def html_to_pdf(request: ConversionRequest) -> Response:
    logger.info(
        "html_to_pdf with %s starting 🏎",
        request.engine,
        extra=get_doc_processing_log_extra(HTML_TO_PDF_ENDPOINT, request.meta),
    )

    if request.engine == "browserless":
        return html_to_pdf_browserless(
            request.url, request.meta, settings.browserless_server_endpoint
        )

    elif request.engine == "wkhtmltopdf":
        return html_to_pdf_wkhtmltopdf(
            request.url, request.meta, settings.iter_chunk_size
        )

    else:
        logger.error(
            "html_to_pdf: or missing engine, requested %s",
            request.engine,
            extra=get_doc_processing_log_extra(HTML_TO_PDF_ENDPOINT, request.meta),
        )
        return Response("Unknown or missing engine", status_code=400)


@app.get("/ping")
def ping():
    return "OK"


@app.exception_handler(HTTPException)
def handle_exception(exc):
    logger.error(
        {
            "message": "HTTPException caught.",
            "exception": exc,
        }
    )
    return JSONResponse(
        {"code": exc.code, "name": exc.name, "description": exc.description},
        status_code=status.HTTP_404_NOT_FOUND,
    )
