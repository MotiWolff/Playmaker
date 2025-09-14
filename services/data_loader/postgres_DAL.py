import psycopg2


class PostgresDAL:
    def __init__(self, postgres_conn:psycopg2.extensions.connection):
        self.postgres_conn = postgres_conn


    def flex_query(self, query:str, if_select:bool):
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
                return f"{query} - successfully executed."

        except Exception as e:
            print(f'failed to execute query to postgres - exception: {e}')


    def upload_table_from_file(self, file_path:str, table_name:str):
        try:
            cur = self.postgres_conn.cursor()

            with open(file_path, "r", encoding="utf-8") as f:
                cur.copy_expert(f"COPY {table_name} FROM STDIN WITH CSV HEADER", f)

            self.postgres_conn.commit()
            cur.close()
            self.postgres_conn.close()

        except Exception as e:
            print(f'failed to upload table from "{file_path}" to postgres, exception:{e}')
