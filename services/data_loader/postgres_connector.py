import psycopg2


class PostgresConnector:
    def __init__(self, host:str, port:str, user:str, password:str, dbname:str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.dbname = dbname


    def connect(self):
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                dbname=self.dbname,
            )
            return conn
        except Exception as e:
            print(f'failed to connect to postgres, exception: {e}')
