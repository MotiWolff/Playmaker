import requests

e = requests.get('https://api.football-data.org/v4/competitions/ll', headers={ 'X-Auth-Token': '8f8a8e658b3f45208a8e916ad1d992eb' })
print(e.content.decode())