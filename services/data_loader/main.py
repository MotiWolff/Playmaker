import os
from manager import Manager
from dotenv import load_dotenv

load_dotenv()

FOOTBALL_DATA_API_KEY = os.getenv('FOOTBALL_DATA_API_KEY')
BASE_URL = os.getenv('BASE_URL')
POSTGRES_URL = os.getenv('POSTGRES_URL')


manager = Manager(api_key=FOOTBALL_DATA_API_KEY, base_url=BASE_URL, postgres_url=POSTGRES_URL)


manager.fetch_and_insert_all()
