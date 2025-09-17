import time
import re
import unicodedata
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from deep_translator import GoogleTranslator
from app.config import settings
from Playmaker.shared.logging.logger import Logger

log = Logger.get_logger(name="playmaker.odds_winner.scraper")

class WinnerScraper:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--lang=he-IL")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        # Use Selenium URL from settings if remote Selenium is used
        self.driver = webdriver.Remote(command_executor=settings.SELENIUM_URL, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 45)
        self.url = settings.SCRAPE_URL
        self.date_format = settings.SCRAPE_DATE_FORMAT
        log.info("scraper.init", extra={"selenium_url": settings.SELENIUM_URL, "url": self.url})

    def clean_text(self, t: str) -> str:
        if not t:
            return ""
        t = unicodedata.normalize("NFKC", t)
        t = re.sub(r"[\u200e\u200f\u202a-\u202e]", "", t)
        return t.strip()

    def safe_float(self, val):
        try:
            return float(val.replace(",", "."))
        except Exception:
            return None

    def translate(self, text: str) -> str:
        try:
            if not text.strip():
                return text
            return GoogleTranslator(source="he", target="en").translate(text)
        except Exception as e:
            log.warning("scraper.translate_failed", extra={"text": text, "error": str(e)})
            return text

    def scrape(self) -> pd.DataFrame:
        t0 = time.perf_counter()
        self.driver.get(self.url)
        # Basic page ready
        try:
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except Exception as e:
            log.warning("scraper.body_wait_failed", extra={"error": str(e)})

        # Wait for odds container
        try:
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".market")))
        except Exception as e:
            log.warning("scraper.market_wait_failed", extra={"error": str(e)})
            try:
                self.driver.save_screenshot("/tmp/winner.png")
                log.info("scraper.screenshot_saved", extra={"path": "/tmp/winner.png"})
            except Exception:
                pass
            self._quit_quiet()
            return pd.DataFrame([])

        all_markets = self.driver.find_elements(By.CSS_SELECTOR, ".market")
        records = []
        today = datetime.now().strftime(self.date_format)

        for market in all_markets:
            try:
                mtype = self.clean_text(market.find_element(By.CSS_SELECTOR, ".market-type").text)
                if "1X2" in mtype and ("סיום" in mtype or "תוצאת סיום" in mtype):
                    league_name = "Unknown League"
                    try:
                        league_name = market.find_element(
                            By.XPATH,
                            ".//ancestor::div[contains(@class,'competition') or contains(@class,'competition-header')][1]"
                        ).text
                        league_name = self.translate(self.clean_text(league_name))
                    except Exception:
                        pass

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

                        home_team = self.translate(self.clean_text(get_name(outcomes[0])))
                        home_odds = self.safe_float(get_ratio(outcomes[0]))
                        draw_odds = self.safe_float(get_ratio(outcomes[1]))
                        away_team = self.translate(self.clean_text(get_name(outcomes[2])))
                        away_odds = self.safe_float(get_ratio(outcomes[2]))

                        records.append({
                            "home_team": home_team,
                            "home_odds": home_odds,
                            "draw_odds": draw_odds,
                            "away_team": away_team,
                            "away_odds": away_odds,
                            "date": today,
                            "league": league_name
                        })
            except Exception as e:
                log.debug("scraper.market_parse_skip", extra={"error": str(e)})
                continue

        if not records:
            try:
                self.driver.save_screenshot("/tmp/winner.png")
                log.info("scraper.screenshot_saved", extra={"path": "/tmp/winner.png"})
            except Exception:
                pass

        self._quit_quiet()
        dt = time.perf_counter() - t0
        log.info("scraper.done", extra={"rows": len(records), "sec": round(dt, 2)})
        return pd.DataFrame(records)

    def _quit_quiet(self):
        try:
            self.driver.quit()
        except Exception:
            pass
