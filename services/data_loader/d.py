import requests
from Playmaker.shared.logging.logger import Logger
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

