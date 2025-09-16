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
        self.driver = webdriver.Remote(
            command_executor=settings.SELENIUM_URL,
            options=chrome_options
        )
        self.wait = WebDriverWait(self.driver, 45)
        self.url = settings.SCRAPE_URL
        self.date_format = settings.SCRAPE_DATE_FORMAT

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
        except Exception:
            return text

    def scrape(self):
        self.driver.get(self.url)
        # Basic page ready
        try:
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except Exception:
            pass
        # Wait for odds container (selector may need adjustment if site changes)
        try:
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".market")))
        except Exception:
            # Save screenshot to help diagnose blank pages/consent screens
            try:
                self.driver.save_screenshot("/tmp/winner.png")
            except Exception:
                pass
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

                    # New DOM: outcomes are under .outcome
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
            except Exception:
                continue

        try:
            if not records:
                # Save a screenshot if nothing parsed
                self.driver.save_screenshot("/tmp/winner.png")
        except Exception:
            pass
        finally:
            try:
                self.driver.quit()
            except Exception:
                pass
        return pd.DataFrame(records)