import logging
import logging.config
import os
import subprocess
import tempfile
from typing import Optional

import requests
from fastapi.responses import JSONResponse, Response
from pydantic import AnyHttpUrl

from processing_tools.logging.config import get_doc_processing_log_extra
from processing_tools.types import HTML_TO_PDF_ENDPOINT, DocumentMeta
from processing_tools.utils import filename_to_pdf_name

logger = logging.getLogger(__name__)


# scale to fit web pages in the browser window
SCALE = 0.5
MARGIN = {"top": "10px", "right": "35px", "bottom": "10px", "left": "35px"}


def html_to_pdf_browserless(
    url: AnyHttpUrl, meta: Optional[DocumentMeta], endpoint: str
) -> Response:
    browserless_url = f"{endpoint}/pdf"
    logger.debug(
        "Transformation started.",
        extra=get_doc_processing_log_extra(HTML_TO_PDF_ENDPOINT, meta),
    )
    params = {
        "url": url,
        "options": {
            "printBackground": True,
            "scale": SCALE,
            "margin": MARGIN,
            # "displayHeaderFooter": True,
            # "format": "A0",
        },
    }
    response = requests.post(browserless_url, json=params)
    if not response.ok:
        logger.warning(
            {
                "message": "Transformation failed.",
                "response": response,
                "url": url,
            }
        )
        return JSONResponse({"detail": response.text}, status_code=response.status_code)

    logger.debug(
        "Transformation completed.",
        extra=get_doc_processing_log_extra(HTML_TO_PDF_ENDPOINT, meta),
    )
    return Response(content=response.content, media_type="application/pdf")


def html_to_pdf_wkhtmltopdf(
    url: AnyHttpUrl, meta: Optional[DocumentMeta], chunk_size: int
) -> Response:
    logger.debug(
        "Transformation started.",
        extra=get_doc_processing_log_extra(HTML_TO_PDF_ENDPOINT, meta),
    )

    # create temp file
    file_handle, temp_path = tempfile.mkstemp()
    web_path = f"{temp_path}.html"
    out_path = filename_to_pdf_name(web_path)

    input_file_response = requests.get(url)
    with open(web_path, "wb") as f:
        for chunk in input_file_response.iter_content(chunk_size=chunk_size):
            f.write(chunk)

    process_args = [
        "wkhtmltopdf",
        # Disable local filesystem access and javascript for security
        "--disable-javascript",
        "--disable-local-file-access",
        web_path,
        out_path,
    ]
    try:
        subprocess.run(
            process_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
        )
    except subprocess.CalledProcessError:
        # Sometimes wkhtmltopdf will fail partially. Unless it fails fully,
        # catch this exception.
        logger.exception(
            "Transformation partially failed.",
            extra=get_doc_processing_log_extra(HTML_TO_PDF_ENDPOINT, meta),
        )
        if not os.path.exists(out_path) or not os.path.getsize(out_path):
            logger.warning(
                "Transformation failed.",
                extra=get_doc_processing_log_extra(HTML_TO_PDF_ENDPOINT, meta),
            )
            raise
    finally:
        os.close(file_handle)
        os.remove(temp_path)
        os.remove(web_path)

    with open(out_path, "rb") as f:
        response_bytes = f.read()
    os.remove(out_path)

    logger.debug(
        "Transformation completed.",
        extra=get_doc_processing_log_extra(HTML_TO_PDF_ENDPOINT, meta),
    )
    return Response(content=response_bytes, media_type="application/pdf")
