import asyncio
import os
import logging
from typing import List, Dict, Any
from arq import create_pool
from arq.connections import RedisSettings

# Set up clean logging output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("Producer")

# Read Redis configuration from environment variables with safe defaults
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))


async def enqueue_jobs(targets: List[Dict[str, Any]]):
    """Connects to Redis queue and dispatches scraping tasks to arq workers."""
    logger.info(f"Connecting to Redis at {REDIS_HOST}:{REDIS_PORT}...")
    redis = await create_pool(RedisSettings(host=REDIS_HOST, port=REDIS_PORT))

    try:
        for target in targets:
            url = target["url"]
            requires_js = target.get("requires_js", False)

            # Enqueue the job matching the function name registered in tasks.py
            job = await redis.enqueue_job("scrape_url_task", url, requires_js)
            
            if job:
                logger.info(f"Successfully enqueued Job ID: '{job.job_id}' for URL: {url}")
            else:
                logger.warning(f"Job was skipped or already present in queue for URL: {url}")

    except Exception as e:
        logger.error(f"Failed to enqueue jobs to Redis: {e}")
    finally:
        # Gracefully close connection pool to prevent hanging sockets
        await redis.aclose()
        logger.info("Redis connection closed cleanly.")


if __name__ == "__main__":
    # Sample target payload to test execution
    sample_targets = [
        {"url": "https://news.ycombinator.com", "requires_js": False},
        {"url": "https://httpbin.org/headers", "requires_js": False},
        {"url": "https://quotes.toscrape.com/js/", "requires_js": True},
    ]

    asyncio.run(enqueue_jobs(sample_targets))
