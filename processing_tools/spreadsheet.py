import asyncio
import logging.config
import os
import subprocess
from pathlib import Path
from typing import Optional

from processing_tools.logging.config import get_doc_processing_log_extra
from processing_tools.types import XLS_TO_XLSX_ENDPOINT, FileConverter

logger = logging.getLogger(__name__)


lock = asyncio.Lock()


class XLSToXLSXConverter(FileConverter):
    async def convert(self, in_path: Path) -> bytes:
        """
        Accepts on xls file and converts it to a xlsx using libreoffice.
        """

        out_path: Optional[str] = None

        async with lock:

            try:
                subprocess.run(
                    [
                        "libreoffice",
                        "--headless",
                        "--convert-to",
                        "xlsx",
                        str(in_path.absolute()),
                        "--outdir",
                        str(in_path.parent),
                    ],
                    # combine stdout and stderr
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    check=True,
                )

                out_path = str(list(in_path.parent.glob("*.xlsx"))[0])

            except subprocess.CalledProcessError as e:
                extra = get_doc_processing_log_extra(XLS_TO_XLSX_ENDPOINT, self.meta)
                extra["error_detail"] = e.stdout.decode("utf-8")
                logger.exception(
                    "%s: called process error",
                    self.__class__.__name__,
                    extra=extra,
                )
                if (
                    not out_path
                    or not os.path.exists(out_path)
                    or not os.path.getsize(out_path)
                ):
                    logger.error(
                        "%s: no file found at out_path",
                        self.__class__.__name__,
                        extra=get_doc_processing_log_extra(
                            XLS_TO_XLSX_ENDPOINT, self.meta
                        ),
                    )
                    raise e
            except IndexError:
                logger.exception(
                    "%s: libreoffice - no xlsx generated",
                    self.__class__.__name__,
                    extra=get_doc_processing_log_extra(XLS_TO_XLSX_ENDPOINT, self.meta),
                )
                raise
            except Exception:
                logger.exception(
                    "%s: unknown error running libreoffice",
                    self.__class__.__name__,
                    extra=get_doc_processing_log_extra(XLS_TO_XLSX_ENDPOINT, self.meta),
                )
                raise

        with open(out_path, "rb") as f:
            response_bytes = f.read()

        return response_bytes
