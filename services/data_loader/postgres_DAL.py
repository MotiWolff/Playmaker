import json

import psycopg2


class PostgresDAL:
    def __init__(self, postgres_conn:psycopg2.extensions.connection):
        self.postgres_conn = postgres_conn
        self.cur = postgres_conn.cursor()


    def flex_query(self, query:str, if_select:bool):
        """
        function to send a query to the postgres
        :param query: the sql query to execute on the postgres.
        :param if_select: if the sql query needs to return values like "SELECT" query.
        :return: if the query is "SELECT" query - return a list of the rows. else - None.
        """
        try:
            self.cur.execute(query)

            if if_select:

                return_rows = []

                rows = self.cur.fetchall()
                for row in rows:
                    return_rows.append(row)

                return return_rows

            else:
                self.postgres_conn.commit()
                self.cur.close()
                print(f"{query} - successfully executed.")

        except Exception as e:
            print(f'failed to execute query to postgres - exception: {e}')

    def insert_competition(self, comp):
        self.cur.execute("""
            INSERT INTO raw_competitions (
                competition_id, name, code, area_name, area_code, type,
                emblem_url, current_season_id, current_season_start_date,
                current_season_end_date, current_matchday,
                number_of_available_seasons, last_updated, api_response_raw
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (competition_id) DO NOTHING
        """, (
            comp.get("id"),
            comp.get("name"),
            comp.get("code"),
            comp.get("area", {}).get("name"),
            comp.get("area", {}).get("id"),
            comp.get("type"),
            comp.get("emblem"),
            (comp.get("currentSeason") or {}).get("id"),
            (comp.get("currentSeason") or {}).get("startDate"),
            (comp.get("currentSeason") or {}).get("endDate"),
            (comp.get("currentSeason") or {}).get("currentMatchday"),
            comp.get("numberOfAvailableSeasons"),
            comp.get("lastUpdated"),
            json.dumps(comp)
        ))

        self.postgres_conn.commit()

    def insert_team(self, team):
        self.cur.execute("""
            INSERT INTO raw_teams (
                team_id, name, short_name, tla, area_name, area_code,
                founded, club_colors, venue, address, website, email, phone,
                crest_url, last_updated, api_response_raw
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (team_id) DO NOTHING
        """, (
            team.get("id"),
            team.get("name"),
            team.get("shortName"),
            team.get("tla"),
            team.get("area", {}).get("name"),
            team.get("area", {}).get("id"),
            team.get("founded"),
            team.get("clubColors"),
            team.get("venue"),
            team.get("address"),
            team.get("website"),
            team.get("email"),
            team.get("phone"),
            team.get("crest"),
            team.get("lastUpdated"),
            json.dumps(team)
        ))
        self.postgres_conn.commit()

    def insert_match(self, match):
        self.cur.execute("""
            INSERT INTO raw_matches (
                match_id, area_id, competition_id, season_id, utc_date, status,
                matchday, stage, group_name, last_updated,
                home_team_id, home_team_name, home_team_short_name, home_team_tla, home_team_crest,
                away_team_id, away_team_name, away_team_short_name, away_team_tla, away_team_crest,
                score_winner, score_duration,
                score_full_time_home, score_full_time_away,
                score_half_time_home, score_half_time_away,
                referees, api_response_raw
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (match_id) DO NOTHING
        """, (
            match.get("id"),
            (match.get("area") or {}).get("id"),
            (match.get("competition") or {}).get("id"),
            (match.get("season") or {}).get("id"),
            match.get("utcDate"),
            match.get("status"),
            match.get("matchday"),
            match.get("stage"),
            match.get("group"),
            match.get("lastUpdated"),
            (match.get("homeTeam") or {}).get("id"),
            (match.get("homeTeam") or {}).get("name"),
            (match.get("homeTeam") or {}).get("shortName"),
            (match.get("homeTeam") or {}).get("tla"),
            (match.get("homeTeam") or {}).get("crest"),
            (match.get("awayTeam") or {}).get("id"),
            (match.get("awayTeam") or {}).get("name"),
            (match.get("awayTeam") or {}).get("shortName"),
            (match.get("awayTeam") or {}).get("tla"),
            (match.get("awayTeam") or {}).get("crest"),
            (match.get("score") or {}).get("winner"),
            (match.get("score") or {}).get("duration"),
            (match.get("score") or {}).get("fullTime", {}).get("home"),
            (match.get("score") or {}).get("fullTime", {}).get("away"),
            (match.get("score") or {}).get("halfTime", {}).get("home"),
            (match.get("score") or {}).get("halfTime", {}).get("away"),
            json.dumps(match.get("referees")),
            json.dumps(match)
        ))

        self.postgres_conn.commit()

    def insert_standing(self, comp_id, season_id, standing):
        self.cur.execute("""
            INSERT INTO raw_standings (
                competition_id, season_id, stage, type, group_name, table_data,
                last_updated, api_response_raw
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            comp_id,
            season_id,
            standing.get("stage"),
            standing.get("type"),
            standing.get("group"),
            json.dumps(standing.get("table")),
            standing.get("lastUpdated"),
            json.dumps(standing)
        ))
        self.postgres_conn.commit()