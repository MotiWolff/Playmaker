import psycopg2


class PostgresDAL:
    def __init__(self, postgres_conn:psycopg2.extensions.connection):
        self.postgres_conn = postgres_conn


    def flex_query(self, query:str, if_select:bool):
        """
        function to send a query to the postgres
        :param query: the sql query to execute on the postgres.
        :param if_select: if the sql query needs to return values like "SELECT" query.
        :return: if the query is "SELECT" query - return a list of the rows. else - None.
        """
        try:
            cur = self.postgres_conn.cursor()
            cur.execute(query)

            if if_select:

                return_rows = []

                rows = cur.fetchall()
                for row in rows:
                    return_rows.append(row)

                return return_rows

            else:
                self.postgres_conn.commit()
                cur.close()
                print(f"{query} - successfully executed.")

        except Exception as e:
            print(f'failed to execute query to postgres - exception: {e}')


    def upload_table_from_file(self, file_path:str, table_name:str):
        """
        get a table from local and create a table on the postgres.
        :param file_path: the table file path.
        :param table_name: the name of the table that will be called on the postgres database.
        :return: None
        """
        try:
            cur = self.postgres_conn.cursor()

            with open(file_path, "r", encoding="utf-8") as f:
                cur.copy_expert(f"COPY {table_name} FROM STDIN WITH CSV HEADER", f)

            self.postgres_conn.commit()
            cur.close()
            self.postgres_conn.close()

            print(f'"{file_path}" table uploaded successfully to postgres under table name: {table_name}')

        except Exception as e:
            print(f'failed to upload table from "{file_path}" to postgres, exception:{e}')
