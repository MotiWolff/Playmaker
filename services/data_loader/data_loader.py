import os
from io import StringIO
import requests
import pandas as pd


class DataLoader:

    @staticmethod
    def download(url:str, saved_file_path:str):
        try:
            if os.path.exists(saved_file_path):
                print(f'file "{saved_file_path}" already exist.')
                return

            data = requests.get(url).content.decode()
            df = pd.read_csv(StringIO(data))

            DataLoader.save_to_csv(file_path=saved_file_path, df=df)

        except Exception as e:
            print(e)

    @staticmethod
    def save_to_csv(file_path:str, df:pd.DataFrame):
        try:

            df.to_csv(file_path, index=False, encoding="utf-8")

        except Exception as e:
            print(e)
