## Improvements for services/data_loader (with code and file paths)

Below are actionable fixes with concrete code snippets and where to place each change.

### 1) Dockerfile: correct entrypoint and install deps
- File: `services/data_loader/Dockerfile`
- Replace CMD and add requirements installation. Option A (recommended, with `requirements.txt`):

```dockerfile
# services/data_loader/Dockerfile
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

RUN pip install --no-cache-dir -U pip

# Copy shared and service code
COPY shared /app/shared
COPY services/data_loader /app/services/data_loader

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Run the correct module (ensure relative imports work)
CMD ["python","-m","services.data_loader.main"]
```

Option B (no requirements file; quick inline install):

```dockerfile
# services/data_loader/Dockerfile (inline deps)
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir requests python-dotenv psycopg2-binary
COPY shared /app/shared
COPY services/data_loader /app/services/data_loader
CMD ["python","-m","services.data_loader.main"]
```

### 2) Add requirements.txt
- File: `requirements.txt` (project root)

```text
requests
python-dotenv
psycopg2-binary
```

### 3) Use package-relative imports and env fallbacks in main
- File: `services/data_loader/main.py`

```python
import os
from dotenv import load_dotenv
from .manager import Manager

load_dotenv()

FOOTBALL_DATA_API_KEY = os.getenv('FOOTBALL_DATA_API_KEY') or os.getenv('FOOTBALL_API_KEY')
BASE_URL = os.getenv('BASE_URL', 'https://api.football-data.org/v4')
POSTGRES_URL = os.getenv('POSTGRES_URL') or os.getenv('DATABASE_URL')

manager = Manager(api_key=FOOTBALL_DATA_API_KEY, base_url=BASE_URL, postgres_url=POSTGRES_URL)
manager.fetch_and_insert_all()

# Optional: explicitly ensure Bundesliga (BL1) and La Liga (PD)
# manager.ensure_competitions_and_teams_by_codes(["BL1", "PD"])
```

### 4) Manager: relative imports and HTTP status checks
- File: `services/data_loader/manager.py`

```python
import requests
from .postgres_connector import PostgresConnector
from .postgres_DAL import PostgresDAL


class Manager:
    def __init__(self, api_key:str, base_url:str, postgres_url:str):
        self.api_key = api_key
        self.base_url = base_url
        self.postgres_url = postgres_url

    def fetch_and_insert_all(self):
        try:
            with PostgresConnector(postgres_url=self.postgres_url) as postgres_conn:
                postgres_dal = PostgresDAL(postgres_conn.connect())
                headers = { 'X-Auth-Token': self.api_key }

                # phase 1 - competitions
                resp = requests.get(f"{self.base_url}/competitions", headers=headers)
                resp.raise_for_status()
                competitions = resp.json()
                for comp in competitions.get("competitions", []):
                    comp_id = comp.get("id")
                    postgres_dal.insert_competition(comp)

                    # phase 2 - teams per competition
                    teams_resp = requests.get(f"{self.base_url}/competitions/{comp_id}/teams", headers=headers)
                    if teams_resp.ok:
                        for t in teams_resp.json().get("teams", []):
                            postgres_dal.insert_team(t)

                    # phase 3 - matches per competition
                    matches_resp = requests.get(f"{self.base_url}/competitions/{comp_id}/matches", headers=headers)
                    if matches_resp.ok:
                        for m in matches_resp.json().get("matches", []):
                            postgres_dal.insert_match(m)

                    # phase 4 - standings per competition
                    standings_resp = requests.get(f"{self.base_url}/competitions/{comp_id}/standings", headers=headers)
                    if standings_resp.ok:
                        season_id = (standings_resp.json().get("season") or {}).get("id")
                        for s in standings_resp.json().get("standings", []):
                            postgres_dal.insert_standing(comp_id, season_id, s)
        except Exception as e:
            print(f'failed to run the manager, exception: {e}')

    # Optional: explicit fetch for specific leagues (avoids missing BL1/PD)
    def ensure_competitions_and_teams_by_codes(self, comp_codes:list[str]):
        headers = { 'X-Auth-Token': self.api_key }
        try:
            with PostgresConnector(postgres_url=self.postgres_url) as postgres_conn:
                postgres_dal = PostgresDAL(postgres_conn.connect())
                for code in comp_codes:
                    comp_resp = requests.get(f"{self.base_url}/competitions/{code}", headers=headers)
                    if not comp_resp.ok:
                        continue
                    comp = comp_resp.json()
                    postgres_dal.insert_competition(comp)
                    comp_id = comp.get("id")
                    if not comp_id:
                        continue
                    teams_resp = requests.get(f"{self.base_url}/competitions/{comp_id}/teams", headers=headers)
                    if teams_resp.ok:
                        for t in teams_resp.json().get("teams", []):
                            postgres_dal.insert_team(t)
        except Exception as e:
            print(f'failed to ensure competitions by codes, exception: {e}')
```

### 5) PostgresConnector: safe close
- File: `services/data_loader/postgres_connector.py`

```python
import psycopg2


class PostgresConnector:
    def __init__(self, postgres_url:str):
        self.postgres_url = postgres_url
        self.conn = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(self.postgres_url)
            return self.conn
        except Exception as e:
            print(f'failed to connect to postgres, exception: {e}')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
```

### 6) Optional: avoid closing cursor in flex_query
- File: `services/data_loader/postgres_DAL.py`
- In `flex_query`, remove `self.cur.close()` to allow re-use (only if you plan to use `flex_query`).

```python
            else:
                self.postgres_conn.commit()
                # Do not close the cursor here if you plan to reuse the DAL instance
                print(f"{query} - successfully executed.")
```

### 7) docker-compose: provide BASE_URL or standardize envs
- File: `shared/docker-compose.yaml` (service: `data-loader`)
- Add `BASE_URL` and optionally standardize the API key and DB URL names, or rely on the fallbacks added in code.

```yaml
  data-loader:
    build:
      context: .
      dockerfile: ./services/data_loader/Dockerfile
    environment:
      # Keep existing vars; add BASE_URL and align names if desired
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
      FOOTBALL_API_KEY: ${FOOTBALL_API_KEY}
      BASE_URL: https://api.football-data.org/v4
      ELASTICSEARCH_HOST: ${ELASTICSEARCH_HOST:-elasticsearch:9200}
      ELASTIC_URL: ${ELASTIC_URL:-http://elasticsearch:9200}
```

---

## Bundesliga and La Liga inclusion
- The loader:
  1) Fetches all competitions via `GET /competitions` and inserts into `raw_competitions`.
  2) For each competition, fetches teams via `GET /competitions/{competition_id}/teams` and inserts into `raw_teams`.
- If BL1 (Bundesliga) or PD (La Liga) are missing due to API paging or timing, call:

```python
# services/data_loader/main.py
manager.ensure_competitions_and_teams_by_codes(["BL1", "PD"])
```

- Duplicates are prevented by the existing `ON CONFLICT DO NOTHING` constraints in the DAL.

```python

import psycopg2
from shared.logging.logger import Logger

class PostgresConnector:
    def __init__(self, postgres_url:str):
        self.postgres_url = postgres_url
        self.conn = None
        self.logger = Logger.get_logger(name="playmaker_data_loader")

    def connect(self):
        try:
            self.conn = psycopg2.connect(self.postgres_url)
            self.logger.info("Connected to Postgres")
            return self.conn
        except Exception as e:
            self.logger.error("Failed to connect to Postgres", extra={"error": str(e)})
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            try:
                self.conn.close()
                self.logger.info("Closed Postgres connection")
            except Exception as e:
                self.logger.warning("Error closing Postgres connection", extra={"error": str(e)})

```


```python
import requests
from shared.logging.logger import Logger
from .postgres_connector import PostgresConnector
from .postgres_DAL import PostgresDAL

class Manager:
    def __init__(self, api_key:str, base_url:str, postgres_url:str):
        self.api_key = api_key
        self.base_url = base_url
        self.postgres_url = postgres_url
        self.logger = Logger.get_logger(name="playmaker_data_loader")

    def fetch_and_insert_all(self):
        try:
            with PostgresConnector(postgres_url=self.postgres_url) as postgres_conn:
                postgres_dal = PostgresDAL(postgres_conn.connect())
                headers = { 'X-Auth-Token': self.api_key }

                resp = requests.get(f"{self.base_url}/competitions", headers=headers)
                resp.raise_for_status()
                competitions = resp.json()

                self.logger.info("Fetched competitions", extra={"count": len(competitions.get("competitions", []))})

                for comp in competitions.get("competitions", []):
                    comp_id = comp.get("id")
                    code = comp.get("code")
                    self.logger.info("Upserting competition", extra={"competition_id": comp_id, "code": code})
                    postgres_dal.insert_competition(comp)

                    teams_resp = requests.get(f"{self.base_url}/competitions/{comp_id}/teams", headers=headers)
                    if not teams_resp.ok:
                        self.logger.warning("Failed fetching teams", extra={"competition_id": comp_id, "status": teams_resp.status_code})
                    else:
                        teams = teams_resp.json().get("teams", [])
                        self.logger.info("Fetched teams", extra={"competition_id": comp_id, "teams_count": len(teams)})
                        for t in teams:
                            postgres_dal.insert_team(t)

                    matches_resp = requests.get(f"{self.base_url}/competitions/{comp_id}/matches", headers=headers)
                    if not matches_resp.ok:
                        self.logger.warning("Failed fetching matches", extra={"competition_id": comp_id, "status": matches_resp.status_code})
                    else:
                        matches = matches_resp.json().get("matches", [])
                        self.logger.info("Fetched matches", extra={"competition_id": comp_id, "matches_count": len(matches)})
                        for m in matches:
                            postgres_dal.insert_match(m)

                    standings_resp = requests.get(f"{self.base_url}/competitions/{comp_id}/standings", headers=headers)
                    if not standings_resp.ok:
                        self.logger.warning("Failed fetching standings", extra={"competition_id": comp_id, "status": standings_resp.status_code})
                    else:
                        standings_json = standings_resp.json()
                        season_id = (standings_json.get("season") or {}).get("id")
                        standings = standings_json.get("standings", [])
                        self.logger.info("Fetched standings", extra={"competition_id": comp_id, "season_id": season_id, "standings_count": len(standings)})
                        for s in standings:
                            postgres_dal.insert_standing(comp_id, season_id, s)

        except Exception as e:
            self.logger.error("Manager run failed", extra={"error": str(e)})
            raise

```


