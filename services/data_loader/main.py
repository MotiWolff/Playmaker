import os
from data_loader import DataLoader
from postgres_connector import PostgresConnector
from postgres_DAL import PostgresDAL


POSTGRES_URL = os.getenv('POSTGRES_URL')
TABLE_NAME = os.getenv('TABLE_NAME')

url_epl_25_26 = 'https://www.football-data.co.uk/mmz4281/2526/E0.csv'
saved_file_path = r"C:\Users\User\Desktop\EPL_25_26.csv"

connector = PostgresConnector(postgres_url=POSTGRES_URL)
conn = connector.connect()

dal = PostgresDAL(postgres_conn=conn)

DataLoader.download(url=url_epl_25_26, saved_file_path=saved_file_path)

dal.upload_table_from_file(file_path=saved_file_path, table_name=TABLE_NAME)
