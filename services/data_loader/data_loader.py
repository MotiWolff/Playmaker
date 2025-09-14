import csv
import os
from io import StringIO

import requests
import pandas as pd

class DataLoader:

    @staticmethod
    def download(url:str):
        try:

            data = requests.get(url).content.decode()
            df = pd.read_csv(StringIO(data))

            DataLoader.save_to_csv(file_path=r"C:\Users\User\Desktop\table_1.csv", df=df)

        except Exception as e:
            print(e)

    @staticmethod
    def save_to_csv(file_path:str, df:pd.DataFrame):
        try:

            df.to_csv(file_path, index=False, encoding="utf-8")

        except Exception as e:
            print(e)
