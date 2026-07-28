import logging
from typing import Dict, Any, Optional
from arq.connections import RedisSettings
from backend.database import init_db, save_scraped_items
from backend.engine import ProductionScraper

logger = logging.getLogger("Worker")


async def startup(ctx: Dict[Any, Any]):
    """Initialize database tables and create worker-level scraper instance."""
    logger.info("Initializing worker dependencies and database connection...")
    await init_db()
    # Instantiate long-lived scraper pool for this worker
    ctx["scraper"] = ProductionScraper(max_concurrent=5)


async def shutdown(ctx: Dict[Any, Any]):
    """Gracefully close HTTP sessions and browser contexts on worker exit."""
    logger.info("Shutting down worker resources...")
    scraper: Optional[ProductionScraper] = ctx.get("scraper")
    if scraper:
        # Calls close() to clean up both curl_cffi and Playwright instances
        await scraper.close()


async def scrape_url_task(ctx: Dict[Any, Any], url: str, requires_js: bool = False) -> Dict[str, Any]:
    """Worker task executed asynchronously via Redis queue."""
    scraper: ProductionScraper = ctx["scraper"]
    logger.info(f"Processing URL task: {url}")

    try:
        result = await scraper.scrape(url=url, requires_js=requires_js)
        if result:
            item_dict = result.model_dump()
            # Save extracted item into PostgreSQL
            await save_scraped_items([item_dict])
            return {"status": "success", "data": item_dict}
        
        logger.warning(f"Failed to scrape content from {url}")
        return {"status": "failed", "url": url, "reason": "No content extracted"}
    except Exception as e:
        logger.exception(f"Unhandled error processing task for {url}: {e}")
        # Re-raising allows arq to track retry counts if configured
        raise e


class WorkerSettings:
    """arq Worker Settings configuration class."""
    functions = [scrape_url_task]
    on_startup = startup
    on_shutdown = shutdown
    # Connects to local Redis; override via environment variable if running in Docker/K8s
    redis_settings = RedisSettings(host="localhost", port=6379)
    max_jobs = 10
