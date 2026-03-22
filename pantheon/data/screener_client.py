import requests
from bs4 import BeautifulSoup
import sqlite3
import json
import time
from loguru import logger
from datetime import datetime, timedelta

class ScreenerClient:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self._logged_in = False
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        self.db_path = "fundamentals_cache.db"
        self._init_cache_db()
        self._login()

    def _init_cache_db(self) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS fundamentals_cache
                    (symbol TEXT PRIMARY KEY, data TEXT, fetched_at TEXT)
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to init fundamentals cache db: {e}")

    def _login(self) -> bool:
        login_url = "https://www.screener.in/login/"
        try:
            resp = self.session.get(login_url, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            
            csrf_token = ""
            csrf_input = soup.find("input", {"name": "csrfmiddlewaretoken"})
            if csrf_input:
                csrf_token = csrf_input.get("value", "")
                
            if not csrf_token:
                logger.warning("Could not find CSRF token for screener login.")
                return False

            payload = {
                "username": self.email,
                "password": self.password,
                "csrfmiddlewaretoken": csrf_token
            }
            
            headers = {"Referer": login_url}
            post_resp = self.session.post(login_url, data=payload, headers=headers, timeout=10)
            
            if "login" not in post_resp.url or ("logout" in post_resp.text.lower() and post_resp.status_code == 200):
                self._logged_in = True
                logger.info("Successfully logged into Screener.")
                return True
            else:
                logger.warning("Screener login failed.")
                return False
                
        except Exception as e:
            logger.error(f"Screener login error: {e}")
            return False

    def get_fundamentals(self, symbol: str) -> dict:
        try:
            # STEP 1: Check SQLite cache
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    "SELECT data FROM fundamentals_cache WHERE symbol = ? AND fetched_at > ?",
                    (symbol.upper(), seven_days_ago)
                )
                row = cursor.fetchone()
                if row:
                    try:
                        return json.loads(row[0])
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            logger.error(f"Cache read error for {symbol}: {e}")

        # STEP 2: If not logged in, try login again
        if not self._logged_in:
            if not self._login():
                return self._empty_fundamentals()

        # STEP 3: Fetch symbol data
        try:
            time.sleep(2)
            url = f"https://www.screener.in/company/{symbol.upper()}/"
            resp = self.session.get(url, timeout=15)
            
            if resp.status_code != 200:
                url = f"https://www.screener.in/company/{symbol.upper()}/consolidated/"
                resp = self.session.get(url, timeout=15)
                
            if resp.status_code != 200:
                logger.warning(f"Failed to fetch Screener data for {symbol}, status: {resp.status_code}")
                return self._empty_fundamentals()
                
            # STEP 4: Parse HTML with BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            ratios_data = self._parse_ratios(soup)
            shareholding_data = self._parse_shareholding(soup)
            
            result = self._empty_fundamentals()
            result.update(ratios_data)
            result.update(shareholding_data)
            
            # STEP 5: Store in SQLite cache
            try:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT OR REPLACE INTO fundamentals_cache VALUES (?, ?, ?)",
                        (symbol.upper(), json.dumps(result), now_str)
                    )
                    conn.commit()
            except Exception as e:
                logger.error(f"Cache write error for {symbol}: {e}")
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to scrape fundamentals for {symbol}: {e}")
            return self._empty_fundamentals()

    def _parse_ratios(self, soup) -> dict:
        result = {
            "pe_ratio": None, "pb_ratio": None, "roe": None,
            "roce": None, "debt_to_equity": None, "dividend_yield": None,
            "revenue_growth": None, "profit_growth": None,
            "current_price": None, "market_cap": None
        }
        try:
            # The ratios list is <ul id="top-ratios"> inside <div id="top">
            # (NOT a <section> — plain div)
            ul = soup.find('ul', id='top-ratios')
            if not ul:
                return result
            for li in ul.find_all('li'):
                name_span = li.find('span', class_='name')
                number_span = li.find('span', class_='number')
                if not name_span or not number_span:
                    continue
                name = name_span.get_text(strip=True)
                raw = number_span.get_text(strip=True).replace(',', '').replace('%', '').strip()
                try:
                    value = float(raw)
                except (ValueError, TypeError):
                    value = None

                if 'Stock P/E'       in name: result['pe_ratio']      = value
                elif 'Book Value'    in name: result['pb_ratio']      = value
                elif 'ROE'           in name: result['roe']            = value
                elif 'ROCE'          in name: result['roce']           = value
                elif 'Debt'          in name: result['debt_to_equity'] = value
                elif 'Dividend'      in name: result['dividend_yield'] = value
                elif 'Current Price' in name: result['current_price']  = value
                elif 'Market Cap'    in name: result['market_cap']     = value
        except Exception as e:
            logger.error(f"_parse_ratios error: {e}")
        return result

    def _parse_shareholding(self, soup: BeautifulSoup) -> dict:
        result = {"promoter_pct": None, "fii_pct": None, "dii_pct": None}
        try:
            section = soup.find('section', {'id': 'shareholding'})
            if section:
                table = section.find('table')
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) > 0:
                            header = cols[0].text.strip().lower()
                            val_text = cols[-1].text.strip().replace('%', '').replace(',', '')
                            
                            try:
                                val = float(val_text) if val_text else None
                            except ValueError:
                                val = None
                                
                            if "promoters" in header or "promoter" in header:
                                result["promoter_pct"] = val
                            elif "fiis" in header or "fii" in header:
                                result["fii_pct"] = val
                            elif "diis" in header or "dii" in header:
                                result["dii_pct"] = val
        except Exception as e:
            logger.error(f"Screener _parse_shareholding error: {e}")
            
        return result

    def _empty_fundamentals(self) -> dict:
        return {
            "pe_ratio": None,
            "pb_ratio": None,
            "roe": None,
            "roce": None,
            "debt_to_equity": None,
            "dividend_yield": None,
            "revenue_growth": None,
            "profit_growth": None,
            "promoter_pct": None,
            "fii_pct": None,
            "dii_pct": None
        }
