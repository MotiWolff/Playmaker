# odds_winner/odds.py
from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from pathlib import Path
import time
import pandas as pd
import sqlite3
import unicodedata
import re

# ✅ project logger
from Playmaker.shared.logging.logger import Logger
log = Logger.get_logger(name="playmaker.odds_winner.script")

# --- CONFIG ---
URL = "https://www.winner.co.il/%D7%9E%D7%A9%D7%97%D7%A7%D7%99%D7%9D/%D7%95%D7%95%D7%99%D7%A0%D7%A8-%D7%9C%D7%99%D7%99%D7%9F/%D7%9B%D7%93%D7%95%D7%A8%D7%92%D7%9C/%D7%90%D7%A0%D7%92%D7%9C%D7%99%D7%94,%D7%9E%D7%95%D7%A2%D7%93%D7%95%D7%A0%D7%99%D7%9D%20%D7%91%D7%99%D7%A0%D7%9C%D7%90%D7%95%D7%9E%D7%99%D7%99%D7%9D/%D7%90%D7%A0%D7%92%D7%9C%D7%99%D7%94$%D7%A4%D7%A8%D7%9E%D7%99%D7%99%D7%A8%20%D7%9C%D7%99%D7%92;%D7%9E%D7%95%D7%A2%D7%93%D7%95%D7%A0%D7%99%D7%9D%20%D7%91%D7%99%D7%A0%D7%9C%D7%90%D7%95%D7%9E%D7%99%D7%99%D7%9D$%D7%9C%D7%99%D7%92%D7%AA%20%D7%94%D7%90%D7%9C%D7%95%D7%A4%D7%95%D7%AA"
TODAY = datetime.now().strftime("%d.%m.%Y")
SQLITE_PATH = Path("winner_odds.db")
SCREENSHOT_PATH = Path("winner_last.png")

# --- HELPERS ---
def safe_float(val):
    try:
        return float(val.replace(",", "."))
    except Exception:
        return None

def clean_text(t: str) -> str:
    if not t:
        return ""
    t = unicodedata.normalize("NFKC", t)
    t = re.sub(r"[\u200e\u200f\u202a-\u202e]", "", t)
    return t.strip()

def expand_all(driver) -> None:
    """Expand accordions/sections; tolerate dynamic DOM."""
    expanded = True
    rounds = 0
    while expanded and rounds < 10:
        expanded = False
        rounds += 1
        elements = driver.find_elements(
            By.CSS_SELECTOR,
            ".competition-header, .league-title, .accordion-toggle, .more-btn"
        )
        for el in elements:
            try:
                attr = f"{el.get_attribute('aria-expanded') or ''} {el.get_attribute('class') or ''}"
                if "false" in attr or "collapsed" in attr or "more-btn" in attr:
                    driver.execute_script("arguments[0].click();", el)
                    time.sleep(0.2)
                    expanded = True
            except Exception:
                continue
    log.debug("odds.expand_done", extra={"rounds": rounds})

# --- SCRAPE ---
def scrape() -> pd.DataFrame:
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--lang=he-IL")

    driver = None
    t0 = time.perf_counter()
    try:
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 30)

        log.info("odds.open_url", extra={"url": URL})
        driver.get(URL)

        try:
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".market")))
        except Exception as e:
            log.warning("odds.wait_markets_failed", extra={"error": str(e)})
            try:
                driver.save_screenshot(str(SCREENSHOT_PATH))
                log.info("odds.screenshot_saved", extra={"path": str(SCREENSHOT_PATH)})
            except Exception:
                pass
            return pd.DataFrame([])

        expand_all(driver)

        # Scroll until stable
        max_attempts, attempts = 20, 0
        last_count = 0
        while attempts < max_attempts:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.2)
            markets_now = driver.find_elements(By.CSS_SELECTOR, ".market")
            if len(markets_now) == last_count:
                attempts += 1
            else:
                attempts = 0
                last_count = len(markets_now)

        all_markets = driver.find_elements(By.CSS_SELECTOR, ".market")
        log.info("odds.markets_found", extra={"count": len(all_markets)})

        # Count full-time 1X2 markets (debug stat)
        fulltime_markets = 0
        for m in all_markets:
            try:
                mtype = clean_text(m.find_element(By.CSS_SELECTOR, ".market-type").text)
                if "1X2" in mtype and ("סיום" in mtype or "תוצאת סיום" in mtype):
                    fulltime_markets += 1
            except Exception:
                continue
        log.debug("odds.fulltime_markets_expected", extra={"count": fulltime_markets})

        # Extract rows
        records = []
        for market in all_markets:
            try:
                mtype = clean_text(market.find_element(By.CSS_SELECTOR, ".market-type").text)
                if "1X2" in mtype and ("סיום" in mtype or "תוצאת סיום" in mtype):
                    # league/competition
                    try:
                        league_name = market.find_element(
                            By.XPATH,
                            ".//ancestor::div[contains(@class,'competition') or contains(@class,'competition-header')][1]"
                        ).text
                        league_name = clean_text(league_name)
                    except Exception:
                        league_name = "Unknown League"

                    # Old vs new DOM structure
                    outcomes = market.find_elements(By.CSS_SELECTOR, ".outcome-container")
                    if len(outcomes) < 3:
                        outcomes = market.find_elements(By.CSS_SELECTOR, ".outcome")
                    if len(outcomes) >= 3:
                        def get_name(el):
                            try:
                                return el.find_element(By.CSS_SELECTOR, ".hasHebrewCharacters").text
                            except Exception:
                                try:
                                    return el.find_element(By.CSS_SELECTOR, ".outcome-name").text
                                except Exception:
                                    return el.text

                        def get_ratio(el):
                            try:
                                return el.find_element(By.CSS_SELECTOR, ".ratio").text
                            except Exception:
                                return ""

                        home_team = clean_text(get_name(outcomes[0]))
                        home_odds = safe_float(get_ratio(outcomes[0]))
                        draw_odds = safe_float(get_ratio(outcomes[1]))
                        away_team = clean_text(get_name(outcomes[2]))
                        away_odds = safe_float(get_ratio(outcomes[2]))

                        records.append((home_team, home_odds, draw_odds, away_team, away_odds, TODAY, league_name))
            except Exception as e:
                log.debug("odds.market_parse_skip", extra={"error": str(e)})
                continue

        dt = round(time.perf_counter() - t0, 2)
        log.info("odds.scrape_done", extra={"rows": len(records), "sec": dt})
        return pd.DataFrame(
            records,
            columns=["HOME_TEAM","HOME_ODDS","DRAW_ODDS","AWAY_TEAM","AWAY_ODDS","DATE","LEAGUE"]
        )
    finally:
        try:
            if driver:
                driver.quit()
        except Exception:
            pass

# --- SQLITE UPSERT ---
def upsert_sqlite(df: pd.DataFrame, db_path: Path = SQLITE_PATH) -> None:
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()

        # Create table if not exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='soccer_odds'")
        table_exists = cursor.fetchone()
        if not table_exists:
            cursor.execute("""
                CREATE TABLE soccer_odds (
                    HOME_TEAM TEXT,
                    HOME_ODDS REAL,
                    DRAW_ODDS REAL,
                    AWAY_TEAM TEXT,
                    AWAY_ODDS REAL,
                    DATE TEXT,
                    LEAGUE TEXT,
                    PRIMARY KEY (HOME_TEAM, AWAY_TEAM, DATE)
                )
            """)
            log.info("sqlite.table_created", extra={"path": str(db_path)})
        else:
            # Add LEAGUE column if missing
            cursor.execute("PRAGMA table_info(soccer_odds)")
            columns = [col[1] for col in cursor.fetchall()]
            if "LEAGUE" not in columns:
                cursor.execute("ALTER TABLE soccer_odds ADD COLUMN LEAGUE TEXT")
                log.info("sqlite.column_added", extra={"column": "LEAGUE"})

        conn.commit()

        # Insert/update rows
        written = 0
        for _, row in df.iterrows():
            conn.execute("""
                INSERT INTO soccer_odds (HOME_TEAM, HOME_ODDS, DRAW_ODDS, AWAY_TEAM, AWAY_ODDS, DATE, LEAGUE)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(HOME_TEAM, AWAY_TEAM, DATE) DO UPDATE SET
                    HOME_ODDS=excluded.HOME_ODDS,
                    DRAW_ODDS=excluded.DRAW_ODDS,
                    AWAY_ODDS=excluded.AWAY_ODDS,
                    LEAGUE=excluded.LEAGUE
                WHERE HOME_ODDS != excluded.HOME_ODDS
                   OR DRAW_ODDS != excluded.DRAW_ODDS
                   OR AWAY_ODDS != excluded.AWAY_ODDS
                   OR LEAGUE != excluded.LEAGUE
            """, tuple(row))
            written += 1

        conn.commit()
        log.info("sqlite.upsert_done", extra={"rows": int(written), "path": str(db_path)})

        # Small debug sample
        try:
            sample = pd.read_sql("SELECT * FROM soccer_odds LIMIT 3", conn)
            log.debug("sqlite.sample_rows", extra={"n": len(sample)})
        except Exception:
            pass
    finally:
        conn.close()

# --- ENTRYPOINT ---
def main():
    log.info("odds.run_start", extra={"date": TODAY})
    df = scrape()
    log.info("odds.scraped_rows", extra={"rows": len(df)})

    if df.empty:
        log.warning("odds.no_rows_scraped")
        return

    # Matches per league (compact)
    try:
        counts = df.groupby("LEAGUE").size().to_dict()
        log.info("odds.per_league_counts", extra={"counts": counts})
    except Exception:
        pass

    upsert_sqlite(df)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.exception("odds.run_failed", extra={"error": str(e)})
        raise
