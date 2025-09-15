# import os
import os

from manager import Manager


FOOTBALL_DATA_API_KEY = os.getenv('FOOTBALL_DATA_API_KEY')
BASE_URL = os.getenv('BASE_URL')
POSTGRES_URL = os.getenv('POSTGRES_URL')


manager = Manager(api_key=FOOTBALL_DATA_API_KEY, base_url=BASE_URL, postgres_url=POSTGRES_URL)






#
# POSTGRES_URL = os.getenv('POSTGRES_URL')
# TABLE_NAME = os.getenv('TABLE_NAME')
#
# url_epl_25_26 = 'https://www.football-data.co.uk/mmz4281/2526/E0.csv'
# saved_file_path = r"C:\Users\User\Desktop\EPL_25_26.csv"
#
# connector = PostgresConnector(postgres_url=POSTGRES_URL)
# conn = connector.connect()
#
# dal = PostgresDAL(postgres_conn=conn)
#
# DataLoader.download(url=url_epl_25_26, saved_file_path=saved_file_path)
#
# dal.upload_table_from_file(file_path=saved_file_path, table_name=TABLE_NAME)
# import requests
#
# url = "https://api.football-data.org/v4/matches"
# headers = { 'X-Auth-Token': '8f8a8e658b3f45208a8e916ad1d992eb' }
# res = requests.get(url, headers=headers)
#
# print(res.json())
# print('########################################')
# url = "https://api.football-data.org/v4/competitions/PL/matches?season=2024"
# res = requests.get(url, headers=headers)
#
# print(res.json())
#
# '''
# CREATE TABLE matches (
#     match_id         INT PRIMARY KEY,
#     matchday         INT NOT NULL,
#     match_date       DATE NOT NULL,
#     match_time       TIME NOT NULL,
#     home_team_id     INT NOT NULL,
#     away_team_id     INT NOT NULL,
#     status           VARCHAR(20),
#     actual_home_score INT,
#     actual_away_score INT,
#     FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
#     FOREIGN KEY (away_team_id) REFERENCES teams(team_id)
# );
# '''
#
# a = {
#     'area': {
#     'id': 2114,
#     'name': 'Italy',
#     'code': 'ITA',
#     'flag': 'https://crests.football-data.org/784.svg'
# },
#     'competition': {
#         'id': 2019,
#         'name': 'Serie A',
#         'code': 'SA',
#         'type': 'LEAGUE',
#         'emblem': 'https://crests.football-data.org/SA.png'
#     },
#     'season': {
#         'id': 2395,
#         'startDate': '2025-08-24',
#         'endDate': '2026-05-24',
#         'currentMatchday': 3,
#         'winner': None
#     },
#     'id': 536841,
#     'utcDate': '2025-09-15T16:30:00Z',
#     'status': 'TIMED',
#     'matchday': 3,
#     'stage': 'REGULAR_SEASON',
#     'group': None,
#     'lastUpdated': '2025-09-15T01:32:00Z',
#     'homeTeam': {
#         'id': 450,
#         'name': 'Hellas Verona FC',
#         'shortName': 'Verona',
#         'tla': 'HVE',
#         'crest': 'https://crests.football-data.org/450.png'
#     },
#     'awayTeam':{
#          'id': 457,
#          'name': 'US Cremonese',
#          'shortName': 'Cremonese',
#          'tla': 'CRE',
#          'crest': 'https://crests.football-data.org/457.png'
#          },
#     'score': {
#         'winner': None,
#         'duration': 'REGULAR',
#         'fullTime': {
#             'home': None,
#             'away': None
#         },
#         'halfTime': {
#             'home': None,
#             'away': None
#         }
#     }, 'odds': {
#     'msg': 'Activate Odds-Package in User-Panel to retrieve odds.'
# },
#     'referees': []
# }
#
# res = res.json()['matches']
#
# match_id = res['id']
# matchday = res['matchday']
# match_date = res['utcDate']
# match_time = res['score']['duration']
# home_team_id = res['homeTeam']['id']
# away_team_id = res['awayTeam']['id']
# status = res['status']
# actual_home_score = res['score']['fullTime']['home']
# actual_away_score = res['score']['fullTime']['away']