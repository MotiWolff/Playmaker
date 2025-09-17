import os
from dotenv import load_dotenv
from Playmaker.shared.logging.logger import Logger
from .manager import Manager

load_dotenv()



logger = Logger.get_logger("playmaker.data_loader.main")


FOOTBALL_DATA_API_KEY = os.getenv('FOOTBALL_DATA_API_KEY') or os.getenv('FOOTBALL_API_KEY')
BASE_URL = os.getenv('BASE_URL', 'https://api.football-data.org/v4')
POSTGRES_URL = os.getenv('POSTGRES_URL') or os.getenv('DATABASE_URL')

logger.info('init the data loader manager...')
manager = Manager(api_key=FOOTBALL_DATA_API_KEY, base_url=BASE_URL, postgres_url=POSTGRES_URL)

logger.info('running the manager..')
manager.fetch_and_insert_all()
