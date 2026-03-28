import sqlite3
import asyncio
from pathlib import Path
import feedparser
import aiohttp
from loguru import logger

from pantheon.config.settings import settings

RSS_FEEDS = [
    "https://economictimes.indiatimes.com/markets/rss.cms",
    "https://www.moneycontrol.com/rss/business.xml",
    "https://www.business-standard.com/rss/markets-104.rss",
    "https://www.livemint.com/rss/markets",
    "https://ndtvprofit.com/business/feed",
    "https://www.financialexpress.com/market/feed/"
]

async def _fetch_feed_with_timeout(session: aiohttp.ClientSession, url: str, timeout: int = 10) -> str:
    """Fetch feed content with timeout."""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            resp.raise_for_status()
            return await resp.text()
    except Exception as e:
        logger.warning(f"Failed to fetch feed {url}: {e}")
        return ""

class NewsClient:
    def __init__(self):
        # Use configurable cache directory
        cache_dir = Path(settings.CACHE_DIR)
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = str(cache_dir / "news_cache.db")
        self._init_db()
        logger.info(f"NewsClient initialized with cache at {self.db_path}")
        
    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS news_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        source TEXT,
                        published_at TEXT,
                        summary TEXT,
                        url TEXT UNIQUE,
                        fetched_at TEXT
                    )
                """)
                # Create index on fetched_at for efficient time-based queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_fetched_at ON news_items(fetched_at)
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize news_cache.db: {e}")

    async def _save_entries(self, feed_url: str, entries: list, source: str) -> int:
        """Save entries to SQLite database (runs in thread pool)."""
        count = 0
        def _save():
            nonlocal count
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for entry in entries:
                    title = entry.get('title', '')
                    url = entry.get('link', '')
                    summary = entry.get('summary', '')[:500]
                    published_at = entry.get('published', '')

                    if not url:
                        continue

                    try:
                        cursor.execute("""
                            INSERT OR IGNORE INTO news_items
                            (title, source, published_at, summary, url, fetched_at)
                            VALUES (?, ?, ?, ?, ?, datetime('now'))
                        """, (title, source, published_at, summary, url))

                        if cursor.rowcount == 1:
                            count += 1
                    except sqlite3.Error as e:
                        logger.error(f"DB insert error for url {url}: {e}")

                conn.commit()
        await asyncio.to_thread(_save)
        return count

    async def poll_and_store(self) -> int:
        """Poll all RSS feeds and store new items asynchronously."""
        count = 0
        async with aiohttp.ClientSession() as session:
            for feed_url in RSS_FEEDS:
                try:
                    # Fetch feed with timeout to prevent hanging
                    feed_content = await _fetch_feed_with_timeout(session, feed_url)
                    if not feed_content:
                        continue
                    parsed = feedparser.parse(feed_content)
                    feed_info = getattr(parsed, 'feed', {})
                    source = feed_info.get('title', feed_url)

                    entries = getattr(parsed, 'entries', [])
                    
                    # Save entries in thread pool to avoid blocking event loop
                    feed_count = await self._save_entries(feed_url, entries, source)
                    count += feed_count
                except Exception as e:
                    logger.warning(f"Error parsing feed {feed_url}: {e}")
                    continue

                # Async delay between feeds
                await asyncio.sleep(0.5)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM news_items
                    WHERE fetched_at < datetime('now', '-72 hours')
                """)
                conn.commit()
        except Exception as e:
            logger.warning(f"Error deleting old items from news_items: {e}")

        logger.info(f"Polled {len(RSS_FEEDS)} feeds, stored {count} new items")
        return count

    def get_news_for_symbol(self, symbol: str, company_name: str, hours: int = 48) -> list[dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Sanitize inputs to prevent LIKE injection
                # Escape SQL wildcards and truncate to reasonable length
                safe_company = company_name.replace("%", "\\%").replace("_", "\\_")[:100]
                safe_symbol = symbol.replace("%", "\\%").replace("_", "\\_")[:20]

                # Use parameterized query to prevent SQL injection
                query = """
                    SELECT title, source, published_at, summary, url
                    FROM news_items
                    WHERE fetched_at > datetime('now', '-' || ? || ' hours')
                    AND (
                        title LIKE ? ESCAPE '\\' OR
                        title LIKE ? ESCAPE '\\' OR
                        summary LIKE ? ESCAPE '\\'
                    )
                    ORDER BY fetched_at DESC
                    LIMIT 20
                """

                cursor.execute(query, (str(hours), f"%{safe_company}%", f"%{safe_symbol}%", f"%{safe_company}%"))
                rows = cursor.fetchall()

                results = []
                for row in rows:
                    results.append({
                        "title": row["title"],
                        "source": row["source"],
                        "published_at": row["published_at"],
                        "summary": row["summary"],
                        "url": row["url"]
                    })
                return results
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return []

    def get_recent_market_news(self, hours: int = 24) -> list[dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Use parameterized query to prevent SQL injection
                query = """
                    SELECT title, source, published_at, summary, url
                    FROM news_items
                    WHERE fetched_at > datetime('now', '-' || ? || ' hours')
                    ORDER BY fetched_at DESC
                    LIMIT 30
                """

                cursor.execute(query, (str(hours),))
                rows = cursor.fetchall()

                results = []
                for row in rows:
                    results.append({
                        "title": row["title"],
                        "source": row["source"],
                        "published_at": row["published_at"],
                        "summary": row["summary"],
                        "url": row["url"]
                    })
                return results
        except Exception as e:
            logger.error(f"Error fetching recent market news: {e}")
            return []
