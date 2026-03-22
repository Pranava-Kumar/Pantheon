import sqlite3
import time
from datetime import datetime
import feedparser
from loguru import logger

RSS_FEEDS = [
    "https://economictimes.indiatimes.com/markets/rss.cms",
    "https://www.moneycontrol.com/rss/business.xml",
    "https://www.business-standard.com/rss/markets-104.rss",
    "https://www.livemint.com/rss/markets",
    "https://ndtvprofit.com/business/feed",
    "https://www.financialexpress.com/market/feed/"
]

class NewsClient:
    def __init__(self):
        self.db_path = "news_cache.db"
        self._init_db()
        logger.info("NewsClient initialized")
        
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
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize news_cache.db: {e}")

    def poll_and_store(self) -> int:
        count = 0
        
        for feed_url in RSS_FEEDS:
            try:
                parsed = feedparser.parse(feed_url)
                feed_info = getattr(parsed, 'feed', {})
                source = feed_info.get('title', feed_url)
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    entries = getattr(parsed, 'entries', [])
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
            except Exception as e:
                logger.warning(f"Error parsing feed {feed_url}: {e}")
                continue
                
            time.sleep(0.5)
            
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
                
                query = f"""
                    SELECT title, source, published_at, summary, url 
                    FROM news_items
                    WHERE fetched_at > datetime('now', '-{hours} hours') 
                    AND (
                        title LIKE ? OR 
                        title LIKE ? OR 
                        summary LIKE ?
                    )
                    ORDER BY fetched_at DESC
                    LIMIT 20
                """
                
                cursor.execute(query, (f"%{company_name}%", f"%{symbol}%", f"%{company_name}%"))
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
                
                query = f"""
                    SELECT title, source, published_at, summary, url
                    FROM news_items
                    WHERE fetched_at > datetime('now', '-{hours} hours')
                    ORDER BY fetched_at DESC
                    LIMIT 30
                """
                
                cursor.execute(query)
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
