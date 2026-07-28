import asyncio
import logging
import random
from typing import Optional, Dict, Any
from pydantic import BaseModel
from selectolax.parser import HTMLParser
from curl_cffi.requests import AsyncSession
from playwright.async_api import async_playwright, Browser, BrowserContext
from playwright_stealth import stealth_async

logger = logging.getLogger("Engine")


class ScrapedItem(BaseModel):
    url: str
    title: str
    price: Optional[str] = None
    meta_description: Optional[str] = None


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


class ProductionScraper:
    def __init__(self, max_concurrent: int = 5, proxy: Optional[str] = None):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.proxy = proxy
        self.browser: Optional[Browser] = None
        self.playwright = None
        self.http_session: Optional[AsyncSession] = None

    async def _get_http_session(self) -> AsyncSession:
        """Reuse HTTP connection pool with proxies attached."""
        if not self.http_session:
            proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
            self.http_session = AsyncSession(proxies=proxies)
        return self.http_session

    async def init_browser(self):
        """Lazy-load Playwright Chromium browser instance."""
        if not self.browser:
            self.playwright = await async_playwright().start()
            launch_args: Dict[str, Any] = {
                "headless": True,
                "args": [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                ],
            }
            if self.proxy:
                launch_args["proxy"] = {"server": self.proxy}
            self.browser = await self.playwright.chromium.launch(**launch_args)

    async def close(self):
        """Clean shutdown for both HTTP session pool and browser engine."""
        if self.http_session:
            await self.http_session.close()
            self.http_session = None

        if self.browser:
            await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            self.browser = None
            self.playwright = None

    async def fetch_static(self, url: str) -> Optional[str]:
        """Engine 1: Fast HTTP request using curl_cffi for TLS browser fingerprint spoofing."""
        async with self.semaphore:
            try:
                session = await self._get_http_session()
                response = await session.get(
                    url,
                    impersonate="chrome120",
                    timeout=12,
                    headers={"User-Agent": random.choice(USER_AGENTS)},
                )
                if response.status_code == 200:
                    return response.text
                logger.warning(f"Static fetch returned HTTP {response.status_code} for {url}")
            except Exception as e:
                logger.error(f"curl_cffi fetch error on {url}: {e}")
            return None

    async def fetch_dynamic(self, url: str, wait_selector: Optional[str] = None) -> Optional[str]:
        """Engine 2: Headless Playwright fetch with stealth masking for JS-heavy sites."""
        async with self.semaphore:
            if not self.browser:
                await self.init_browser()

            context: Optional[BrowserContext] = None
            page = None
            try:
                assert self.browser is not None
                context = await self.browser.new_context(
                    user_agent=random.choice(USER_AGENTS),
                    viewport={"width": 1920, "height": 1080},
                )
                page = await context.new_page()
                await stealth_async(page)

                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                if wait_selector:
                    await page.wait_for_selector(wait_selector, timeout=10000)

                return await page.content()
            except Exception as e:
                logger.error(f"Playwright fetch error for {url}: {e}")
                return None
            finally:
                if page:
                    await page.close()
                if context:
                    await context.close()

    def parse_html(self, html_content: str, url: str) -> Optional[ScrapedItem]:
        """Fast C-based HTML parsing via Selectolax with resilient selector fallback."""
        if not html_content:
            return None

        tree = HTMLParser(html_content)
        title_node = tree.css_first("title")
        title = title_node.text(strip=True) if title_node else "No Title Found"

        meta_node = tree.css_first('meta[name="description"], meta[property="og:description"]')
        meta_desc = (
            meta_node.attributes.get("content", "").strip()
            if (meta_node and meta_node.attributes)
            else None
        )

        price = None
        for selector in [".price", "#price", "span.amount", "[data-price]", ".product-price"]:
            price_node = tree.css_first(selector)
            if price_node and price_node.text(strip=True):
                price = price_node.text(strip=True)
                break

        return ScrapedItem(url=url, title=title, price=price, meta_description=meta_desc)

    async def scrape(self, url: str, requires_js: bool = False) -> Optional[ScrapedItem]:
        """Routing pipeline with automatic dynamic browser fallback."""
        html = await self.fetch_dynamic(url) if requires_js else await self.fetch_static(url)

        if not html and not requires_js:
            logger.info(f"Static request failed for {url}. Falling back to Browser...")
            html = await self.fetch_dynamic(url)

        return self.parse_html(html, url) if html else None
