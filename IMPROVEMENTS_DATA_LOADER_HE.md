## הצעות לשיפור למודול data_loader

להלן ממצאים והמלצות ליישור קו והקשחה של השירות `services/data_loader` מול שאר הפרויקט וסביבת ההרצה.

### 1) נקודת כניסה והרצה ב-Docker
- המצב כיום: ב-`Dockerfile` מוגדר `CMD ["python","-m","services.data_loader"]`, אך אין `__main__` ב-`services/data_loader/__init__.py`, ולכן לא ירוץ כלום.
- מומלץ:
  - לשנות ל-`python -m services.data_loader.main`, או
  - להוסיף לוגיקה ב-`__init__.py` שמפעילה את `main.py`, או
  - להריץ ישירות את הקובץ `python services/data_loader/main.py`.

### 2) שמות משתני סביבה (ENV) לא עקביים
- המצב כיום בקוד (`main.py`):
  - `FOOTBALL_DATA_API_KEY`, `BASE_URL`, `POSTGRES_URL`.
- המצב ב-Compose: `FOOTBALL_API_KEY`, `DATABASE_URL` (ולא מוגדר `BASE_URL`).
- מומלץ:
  - להוסיף Fallbacks בקוד: לקרוא `FOOTBALL_DATA_API_KEY or FOOTBALL_API_KEY`, `POSTGRES_URL or DATABASE_URL`.
  - להגדיר `BASE_URL` עם ברירת מחדל (למשל: `https://api.football-data.org/v4`).
  - לשקול ליישר בין שמות המשתנים בקוד וב-Compose כדי להפחית בלבול.

### 3) תלותים (dependencies) חסרים בתמונה
- הקוד משתמש ב-`requests`, `python-dotenv`, ו-`psycopg2`. בתמונת `python:3.11-slim` אין זאת כברירת מחדל.
- מומלץ:
  - להוסיף התקנת חבילות. הפתרון הפשוט: `psycopg2-binary` במקום `psycopg2`.
  - ליצור `requirements.txt` ולבצע `pip install -r requirements.txt` (למשל: `requests`, `python-dotenv`, `psycopg2-binary`).
  - אם מתעקשים על `psycopg2` הלא-בינארית: להתקין `gcc` ו-`libpq-dev` לפני `pip install`.

### 4) יבוא יחסי בתוך החבילה
- כיום:
  - `main.py`: `from manager import Manager`
  - `manager.py`: `from postgres_connector import PostgresConnector`, `from postgres_DAL import PostgresDAL`
- במצב הרצה כמודול (`-m`) היבוא הזה עלול להישבר.
- מומלץ: להחליף ליבוא יחסי: `from .manager import Manager`, `from .postgres_connector import PostgresConnector`, `from .postgres_DAL import PostgresDAL`.

### 5) dotenv בתוך קונטיינר
- `load_dotenv()` לא מזיק, אבל אין `.env` בתמונה. ב-Compose ממילא מעבירים ENV. לשמור או להסיר – לשיקולכם, אך לא לסמוך עליו בקונטיינר.

### 6) טיפול בשגיאות HTTP וקצבי תעבורה
- כיום יש הנחה ש-`requests.get(...).json()` תמיד מצליח. אין בדיקת `status_code`, אין התמודדות עם 429/5xx.
- מומלץ:
  - להשתמש ב-`resp.raise_for_status()` או לבדוק `resp.ok` לפני `.json()`.
  - להוסיף Retry עם backoff (למשל עם `tenacity` או מימוש פשוט), במיוחד ל-429.
  - לשקול השהייה קצרה בין קריאות רצופות כדי להפחית Rate Limiting.

### 7) סגירת חיבורים ולוגינג
- `PostgresConnector.__exit__` קורא `self.conn.close()` ללא בדיקת `None`.
  - מומלץ: `if self.conn: self.conn.close()`.
- יש שימוש ב-`print` לשגיאות. בפרויקט יש תשתית לוגינג ב-`shared.logging.logger` – מומלץ לאחד לשם עקביות וניטור.

### 8) `flex_query` סוגר Cursor
- ב-`PostgresDAL.flex_query` נסגר ה-`cursor` בפעולות לא-SELECT, מה שעלול לשבור שימוש חוזר באובייקט.
- מאחר והפונקציה לא בשימוש בקוד הנוכחי – או להסיר אותה, או לא לסגור שם Cursor.

### 9) סכמת בסיס הנתונים
- המודול מכניס לטבלאות: `raw_competitions`, `raw_teams`, `raw_matches`, `raw_standings`.
- אין מיגרציות/DDL במודול. יש לוודא שהטבלאות נוצרות לפני הרצת ה-Loader (למשל באמצעות כלי מיגרציות או Script Init של Postgres).
- מומלץ להוסיף אינדקסים על מפתחות עיקריים/זרים (למשל `competition_id`, `team_id`, `match_id`, `season_id`).

### 10) תלות ב-Kafka ב-Compose
- `data-loader` מוגדר כ-`depends_on` על Kafka, אך אינו משתמש בקפקא. ניתן להסיר כדי לקצר זמן עלייה ותלויות מיותרות.

### 11) עמידות נתונים ושדות JSON
- שימוש ב-`json.dumps(...)` כאשר הערך עלול להיות `None` הוא תקין, אך ודאו שמבנה השדות תואם לטיפוסי העמודות (למשל עמודות JSONB/Postgres).
- קיימת הגנה טובה עם `ON CONFLICT DO NOTHING` להימנעות מכפילויות.

### 12) ברירות מחדל מומלצות
- `BASE_URL`: `https://api.football-data.org/v4`.
- `FOOTBALL_DATA_API_KEY`: קריאה גם ל-`FOOTBALL_API_KEY` אם הראשון לא קיים.
- `POSTGRES_URL`: קריאה גם ל-`DATABASE_URL` אם הראשון לא קיים.

### 13) הצעה ל-minimal set של תיקונים מהירים
- לשנות `Dockerfile` להרצת המודול הנכון.
- להתקין `requests`, `python-dotenv`, `psycopg2-binary`.
- לעדכן יבוא יחסי ב-`main.py` ו-`manager.py`.
- להוסיף Fallbacks למשתני הסביבה והגדרת `BASE_URL`.
- להוסיף בדיקת `resp.raise_for_status()`.
- להקשיח סגירת חיבור פוסטגרס וביטול `print` לטובת Logger המשותף.

---

## תשובה לשאלה: לה ליגה והבונדסליגה
- הקוד מבצע:
  1) שליפה של כל התחרויות דרך `GET /competitions` והכנסה ל-`raw_competitions`.
  2) עבור כל תחרות שנשלפה – שליפת קבוצות דרך `GET /competitions/{competition_id}/teams` והכנסה ל-`raw_teams`.
- אין בקוד סינון לפי ליגות, לכן אם ה-API מחזיר את התחרויות של לה ליגה (לרוב `PD`) והבונדסליגה (לרוב `BL1`), הן יוכנסו לטבלת `raw_competitions`, והקבוצות שלהן יוכנסו ל-`raw_teams`.
- תנאי לכך: שה-`BASE_URL` וה-API Key תקינים, ושסכמת הטבלאות קיימת בבסיס הנתונים לפני הריצה.


def ensure_competitions_and_teams_by_codes(self, comp_codes:list[str]):
        """
        Explicitly ensure specific competitions (by API code like 'BL1', 'PD') and their teams are loaded.
        Relies on ON CONFLICT DO NOTHING in DAL to avoid duplicates for competitions/teams.
        """
        headers = { 'X-Auth-Token': self.api_key }
        try:
            with PostgresConnector(postgres_url=self.postgres_url) as postgres_conn:
                postgres_dal = PostgresDAL(postgres_conn.connect())

                for code in comp_codes:
                    # fetch competition by code (e.g., BL1 for Bundesliga, PD for La Liga)
                    comp_resp = requests.get(f"{self.base_url}/competitions/{code}", headers=headers)
                    if not comp_resp.ok:
                        print(f"failed to fetch competition {code}, status={comp_resp.status_code}")
                        continue
                    comp = comp_resp.json()

                    # insert competition (id is inside the response)
                    postgres_dal.insert_competition(comp)

                    comp_id = comp.get("id")
                    if not comp_id:
                        continue

                    # fetch teams for this competition (current season by default)
                    teams_resp = requests.get(f"{self.base_url}/competitions/{comp_id}/teams", headers=headers)
                    if not teams_resp.ok:
                        print(f"failed to fetch teams for competition {code} (id={comp_id}), status={teams_resp.status_code}")
                        continue
                    for t in teams_resp.json().get("teams", []):
                        postgres_dal.insert_team(t)

        except Exception as e:
            print(f'failed to ensure competitions by codes, exception: {e}')

# Explicitly ensure Bundesliga (BL1) and La Liga (PD) are present, without duplicates
manager.ensure_competitions_and_teams_by_codes(["BL1", "PD"])