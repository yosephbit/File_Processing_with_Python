import asyncio
import logging
import sys
import time

import aiohttp  # type: ignore

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


async def request_office_convert(session, idx):
    t1 = time.time()
    async with session.post(
        "http://ptools:8080/od_to_pdf/",
        json={"url": "http://test_server:8081/big-powerpoint.pptx"},
    ) as resp:
        time_to_post = time.time() - t1
        logger.info(
            "job %d finished in %f seconds (status %d)", idx, time_to_post, resp.status
        )


async def main(count: int):
    t1 = time.time()
    logger.info("starting all")
    async with aiohttp.ClientSession() as session:
        tasks = []
        for idx in range(count):
            tasks.append(asyncio.ensure_future(request_office_convert(session, idx)))
        await asyncio.gather(*tasks)
        logger.info("total time was %s", time.time() - t1)


if __name__ == "__main__":
    count = 5
    if len(sys.argv) == 2:
        count = int(sys.argv[1])
    asyncio.run(main(count))
