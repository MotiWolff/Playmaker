import psycopg2


class PostgresConnector:
    def __init__(self, postgres_url:str):
        self.postgres_url = postgres_url


    def connect(self):
        try:
            conn = psycopg2.connect(self.postgres_url)
            return conn

        except Exception as e:
            print(f'failed to connect to postgres, exception: {e}')
