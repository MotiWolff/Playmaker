import requests
from postgres_connector import PostgresConnector
from postgres_DAL import PostgresDAL



class Manager:
    def __init__(self, api_key:str, base_url:str, postgres_url:str):
        self.api_key = api_key
        self.base_url = base_url
        self.postgres_url = postgres_url
        self.postgres_conn = PostgresConnector(postgres_url=postgres_url).connect()
        self.postgres_dal = PostgresDAL(self.postgres_conn)


    # @staticmethod
    # def competition_json(res:dict):
    #     try:
    #         competition_json = {
    #                     'competition_id' : res['id'],
    #                     'name' : res['name'],
    #                     'code' : res['code'],
    #                     'country' : res['area']['name'],
    #                     'competition_type' : res['type'],
    #                     'season' : res['currentSeason']['id'],
    #                     'current_matchday' : res['currentSeason']['currentMatchday']
    #         }
    #         # created_at = res['']
    #         return competition_json
    #
    #     except Exception as e:
    #         print(f'failed to create the competition json, exception: {e}')


    # def run(self, url_suffixes_list:list[str]):
    #     with PostgresConnector(self.postgres_url) as post_conn:
    #         post_dal = PostgresDAL(post_conn.conn)
    #
    #         for suffix in url_suffixes_list:
    #
    #             if suffix == 'competitions':
    #                data = self.fetcher.get_json_data(url_suffix=suffix)
    #                competition_json = self.competition_json(res=data)
    #
    #             elif suffix == 'teams':
    #                 data = self.fetcher.get_json_data(url_suffix=suffix)
    #                 competition_json = self.competition_json(res=data)

    def fetch_and_insert_all(self):
        headers = { 'X-Auth-Token': self.api_key }
        # שלב 1 – משוך את כל התחרויות
        competitions = requests.get(f"{self.base_url}/competitions", headers=headers).json()
        for comp in competitions.get("competitions", []):
            comp_id = comp.get("id")
            self.postgres_dal.insert_competition(comp)

            # שלב 2 – קבוצות של התחרות
            teams_resp = requests.get(f"{self.base_url}/competitions/{comp_id}/teams", headers=headers).json()
            for t in teams_resp.get("teams", []):
                self.postgres_dal.insert_team(t)

            # שלב 3 – משחקים של התחרות
            matches_resp = requests.get(f"{self.base_url}/competitions/{comp_id}/matches", headers=headers).json()
            for m in matches_resp.get("matches", []):
                self.postgres_dal.insert_match(m)

            # שלב 4 – טבלאות (standings) של התחרות
            standings_resp = requests.get(f"{self.base_url}/competitions/{comp_id}/standings", headers=headers).json()
            for s in standings_resp.get("standings", []):
                season_id = (standings_resp.get("season") or {}).get("id")
                self.postgres_dal.insert_standing(comp_id, season_id, s)

            self.postgres_conn.commit()


