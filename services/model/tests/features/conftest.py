import pandas as pd
import pytest

@pytest.fixture
def small_df():
    # 6 משחקים בין A/B/C כדי לאפשר rolling פשוט
    rows = [
        {"Date":"2021-08-01","HomeTeam":"A","AwayTeam":"B","FTHG":1,"FTAG":0,"FTR":"H","B365H":2.0,"B365D":3.4,"B365A":3.6},
        {"Date":"2021-08-02","HomeTeam":"B","AwayTeam":"A","FTHG":2,"FTAG":2,"FTR":"D","B365H":2.2,"B365D":3.2,"B365A":3.0},
        {"Date":"2021-08-03","HomeTeam":"A","AwayTeam":"C","FTHG":0,"FTAG":1,"FTR":"A","B365H":1.9,"B365D":3.5,"B365A":4.0},
        {"Date":"2021-08-04","HomeTeam":"C","AwayTeam":"A","FTHG":1,"FTAG":3,"FTR":"A","B365H":2.6,"B365D":3.1,"B365A":2.7},
        {"Date":"2021-08-05","HomeTeam":"B","AwayTeam":"C","FTHG":0,"FTAG":0,"FTR":"D","B365H":2.4,"B365D":3.0,"B365A":3.1},
        {"Date":"2021-08-06","HomeTeam":"C","AwayTeam":"B","FTHG":2,"FTAG":1,"FTR":"H","B365H":2.1,"B365D":3.3,"B365A":3.2},
    ]
    return pd.DataFrame(rows)
