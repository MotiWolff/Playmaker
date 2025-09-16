from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import pandas as pd
import sqlite3
import unicodedata
import re

# --- CONFIG ---
url = "https://www.winner.co.il/%D7%9E%D7%A9%D7%97%D7%A7%D7%99%D7%9D/%D7%95%D7%95%D7%99%D7%A0%D7%A8-%D7%9C%D7%99%D7%99%D7%9F/%D7%9B%D7%93%D7%95%D7%A8%D7%92%D7%9C/%D7%90%D7%A0%D7%92%D7%9C%D7%99%D7%94,%D7%9E%D7%95%D7%A2%D7%93%D7%95%D7%A0%D7%99%D7%9D%20%D7%91%D7%99%D7%A0%D7%9C%D7%90%D7%95%D7%9E%D7%99%D7%99%D7%9D/%D7%90%D7%A0%D7%92%D7%9C%D7%99%D7%94$%D7%A4%D7%A8%D7%9E%D7%99%D7%99%D7%A8%20%D7%9C%D7%99%D7%92;%D7%9E%D7%95%D7%A2%D7%93%D7%95%D7%A0%D7%99%D7%9D%20%D7%91%D7%99%D7%A0%D7%9C%D7%90%D7%95%D7%9E%D7%99%D7%99%D7%9D$%D7%9C%D7%99%D7%92%D7%AA%20%D7%94%D7%90%D7%9C%D7%95%D7%A4%D7%95%D7%AA"
today = datetime.now().strftime('%d.%m.%Y')

# --- SELENIUM SETUP ---
chrome_options = Options()
chrome_options.add_argument("--headless=new")
driver = webdriver.Chrome(options=chrome_options)
driver.get(url)

wait = WebDriverWait(driver, 20)
wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".market")))

# --- HELPERS ---
def safe_float(val):
    try:
        return float(val.replace(",", "."))
    except:
        return None

def clean_text(t: str) -> str:
    if not t:
        return ""
    t = unicodedata.normalize("NFKC", t)
    t = re.sub(r"[\u200e\u200f\u202a-\u202e]", "", t)
    return t.strip()

# --- EXPAND ALL SECTIONS ---
def expand_all():
    expanded = True
    while expanded:
        expanded = False
        elements = driver.find_elements(By.CSS_SELECTOR, ".competition-header, .league-title, .accordion-toggle, .more-btn")
        for el in elements:
            try:
                if el.get_attribute("aria-expanded") == "false" or "collapsed" in el.get_attribute("class") or "more-btn" in el.get_attribute("class"):
                    driver.execute_script("arguments[0].click();", el)
                    time.sleep(0.3)
                    expanded = True
            except:
                continue

expand_all()

# --- SCROLL UNTIL STABLE ---
max_attempts, attempts = 20, 0
last_count = 0
while attempts < max_attempts:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    markets_now = driver.find_elements(By.CSS_SELECTOR, ".market")
    if len(markets_now) == last_count:
        attempts += 1
    else:
        attempts = 0
        last_count = len(markets_now)

# --- DEBUG: Count total markets ---
all_markets = driver.find_elements(By.CSS_SELECTOR, ".market")
print(f"Total markets found on page: {len(all_markets)}")

fulltime_markets = 0
for market in all_markets:
    try:
        mtype = clean_text(market.find_element(By.CSS_SELECTOR, ".market-type").text)
        if "1X2" in mtype and ("סיום" in mtype or "תוצאת סיום" in mtype):
            fulltime_markets += 1
    except:
        continue
print(f"Total 1X2 full-time markets expected: {fulltime_markets}")

# --- SCRAPE MARKETS ---
records = []
for market in all_markets:
    try:
        mtype = clean_text(market.find_element(By.CSS_SELECTOR, ".market-type").text)
        if "1X2" in mtype and ("סיום" in mtype or "תוצאת סיום" in mtype):
            # Get nearest league/competition name using XPath
            try:
                league_name = market.find_element(
                    By.XPATH,
                    ".//ancestor::div[contains(@class,'competition') or contains(@class,'competition-header')][1]"
                ).text
                league_name = clean_text(league_name)
            except:
                league_name = "Unknown League"

            outcomes = market.find_elements(By.CSS_SELECTOR, ".outcome-container")
            if len(outcomes) >= 3:
                home_team = outcomes[0].find_element(By.CSS_SELECTOR, ".hasHebrewCharacters").text
                home_odds = safe_float(outcomes[0].find_element(By.CSS_SELECTOR, ".ratio").text)
                draw_odds = safe_float(outcomes[1].find_element(By.CSS_SELECTOR, ".ratio").text)
                away_team = outcomes[2].find_element(By.CSS_SELECTOR, ".hasHebrewCharacters").text
                away_odds = safe_float(outcomes[2].find_element(By.CSS_SELECTOR, ".ratio").text)
                records.append((home_team, home_odds, draw_odds, away_team, away_odds, today, league_name))
    except:
        continue

driver.quit()

# --- DATAFRAME ---
df = pd.DataFrame(records, columns=["HOME_TEAM","HOME_ODDS","DRAW_ODDS","AWAY_TEAM","AWAY_ODDS","DATE","LEAGUE"])
print(f"\n✅ Scraped {len(df)} matches\n")
print("Matches per league:")
print(df.groupby("LEAGUE").size())

# --- SQLITE ---
conn = sqlite3.connect("winner_odds.db")
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
else:
    # Add LEAGUE column if missing
    cursor.execute("PRAGMA table_info(soccer_odds)")
    columns = [col[1] for col in cursor.fetchall()]
    if "LEAGUE" not in columns:
        cursor.execute("ALTER TABLE soccer_odds ADD COLUMN LEAGUE TEXT")

conn.commit()

# Insert/update rows
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

conn.commit()
print("\nSaved to SQL (winner_odds.db, table: soccer_odds). Example rows:")
print(pd.read_sql("SELECT * FROM soccer_odds", conn))
conn.close()

# --- DEBUG SUMMARY ---
print("\n--- Debug Summary ---")
print(f"Total markets found: {len(all_markets)}")
print(f"1X2 full-time markets expected: {fulltime_markets}")
print(f"Matches actually scraped: {len(records)}")
