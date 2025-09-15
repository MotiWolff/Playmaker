import requests
from postgres_connector import PostgresConnector
from postgres_DAL import PostgresDAL



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

                # phase 1 - get all the competitions
                competitions = requests.get(f"{self.base_url}/competitions", headers=headers).json()
                for comp in competitions.get("competitions", []):
                    comp_id = comp.get("id")
                    postgres_dal.insert_competition(comp)

                    # phase 2 - get all the teams in the competition
                    teams_resp = requests.get(f"{self.base_url}/competitions/{comp_id}/teams", headers=headers).json()
                    for t in teams_resp.get("teams", []):
                        postgres_dal.insert_team(t)

                    # phase 3 - matches of the competition
                    matches_resp = requests.get(f"{self.base_url}/competitions/{comp_id}/matches", headers=headers).json()
                    for m in matches_resp.get("matches", []):
                        postgres_dal.insert_match(m)

                    # phase 4 - standing of the competition
                    standings_resp = requests.get(f"{self.base_url}/competitions/{comp_id}/standings", headers=headers).json()
                    for s in standings_resp.get("standings", []):
                        season_id = (standings_resp.get("season") or {}).get("id")
                        postgres_dal.insert_standing(comp_id, season_id, s)


        except Exception as e:
            print(f'failed to run the manager, exception: {e}')

