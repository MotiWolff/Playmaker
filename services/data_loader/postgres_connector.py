import psycopg2


class PostgresConnector:
    def __init__(self, postgres_url:str):
        self.postgres_url = postgres_url
        self.conn = None


    def connect(self):
        try:
            self.conn = psycopg2.connect(self.postgres_url)
            return self.conn

        except Exception as e:
            print(f'failed to connect to postgres, exception: {e}')


    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

