import requests
import dateutil.parser
import pytz
from datetime import datetime

params = (
    ('classificationName', 'music'),
    ('dmaId', '249'),
    ('apikey', 'TC9A3O0V0EmuCwGVTcGGqXP4Nc8yqsVr'),
    ('size', '200'),
)

response = requests.get('https://app.ticketmaster.com/discovery/v2/events.json', params=params)

data = response.json()
for e in data["_embedded"]["events"]:
  name = e["name"]
  genre = "Undefined"
  if len(e["classifications"]) > 0:
    genre = e["classifications"][0]["genre"]["name"]
  venue_obj = e["_embedded"]["venues"][0]
  venue = venue_obj["name"]
  location = str(venue_obj["location"])
  artists = [a["name"] for a in e["_embedded"]["attractions"]]

  ts = 0
  try:
    date_obj = dateutil.parser.parse(e["dates"]["start"]["dateTime"]).replace(tzinfo=None)
    tz = pytz.timezone("America/Chicago")
    dt_with_tz = tz.localize(date_obj, is_dst=None)
    ts = (dt_with_tz - datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds()
  except:
    pass
  print(name, "|", genre, "|", venue, "|", location, artists, ts)

# Old scraping
'''
import requests

params = (
    ('app_key', 'GHM3Vx2vJtSWPvJ6'),
    ('category', 'music'),
    ('l', 'chicago'),
    ('page_size', '200'),
)

response = requests.get('http://api.eventful.com/json/events/search', params=params)

data = response.json()
for e in data["events"]["event"]:
  if e["performers"] is not None:
    p = e["performers"]["performer"]
    if isinstance(p, list):
      p = p[0]
    print(e["title"] + " : " + p["name"])
  
'''