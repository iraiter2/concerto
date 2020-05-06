from flask import Blueprint, Response, abort, redirect, render_template, request
from flask_login import login_required, login_user, logout_user, current_user
from urllib.parse import urlparse, urljoin
from utils import get_db, get_neo_db, get_user
import hashlib
import os
import base64
import json
import requests
import dateutil.parser
import pytz
from datetime import datetime
import time

app = Blueprint('carpool', __name__, template_folder='templates')


@app.route("/reset")
def reset():
    get_db().begin()
    try:
        get_db()["concerts"].delete()
        get_db()["concert_artists"].delete()
        get_db()["carpools"].delete()
        get_db()["carpool_members"].delete()
        get_db()["chat_messages"].delete()
        get_db().commit()
    except Exception as e:
        get_db().rollback()
        return abort(401, "Fail")

    with get_neo_db().session() as session:
          for record in session.run("MATCH (a) DETACH DELETE a"):
            pass
    return "Success"

@app.route("/load_concerts")
def load_concerts():
    params = (
        ('classificationName', 'music'),
        ('dmaId', '249'),
        ('apikey', 'TC9A3O0V0EmuCwGVTcGGqXP4Nc8yqsVr'),
        ('size', '200'),
    )

    response = requests.get('https://app.ticketmaster.com/discovery/v2/events.json', params=params)

    get_db().begin()
    try:
        #get_db()["concerts"].delete()
        #get_db()["concert_artists"].delete()
        data = response.json()
        for e in data["_embedded"]["events"]:
            name = e["name"]
            genre = "Undefined"
            if len(e["classifications"]) > 0:
                genre = e["classifications"][0]["genre"]["name"]
            venue_obj = e["_embedded"]["venues"][0]
            venue = venue_obj["name"]
            location = venue_obj["location"]
            artists = [a["name"] for a in e["_embedded"]["attractions"]]

            ts = 0
            try:
                date_obj = dateutil.parser.parse(e["dates"]["start"]["dateTime"]).replace(tzinfo=None)
                tz = pytz.timezone("America/Chicago")
                dt_with_tz = tz.localize(date_obj, is_dst=None)
                ts = (dt_with_tz - datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds()
            except:
                pass

            lookup = get_db()["concerts"].find_one(name=name, time=ts)
            if lookup is not None:
                continue
            pk = get_db()["concerts"].insert({
                "genre": genre,
                "time": ts,
                "name": name,
                "location": json.dumps(location),
                "venue": venue
            })
            for artist in artists:
                get_db()["concert_artists"].insert({
                    "artist": artist,
                    "concert": pk
                })
            with get_neo_db().session() as session:
              for record in session.run(
                "MERGE (c:Concert {id:$for_id, location:point({latitude:$lat, longitude:$lon})}) ",
                lat=float(location["latitude"]),
                lon=float(location["longitude"]),
                for_id=pk):
                pass
        get_db().commit()
    except Exception as e:
        get_db().rollback()
        return abort(401, "Fail")
    return "Success"

@app.route("/search", methods=["GET"])
@login_required
def search():
    artist = request.args.get("artist").lower()
    r = get_db().query('SELECT * FROM concerts WHERE LOWER(name) LIKE :artist ORDER BY name', artist="%{}%".format(artist))
    return json.dumps([x for x in r])

@app.route("/carpool/create", methods=["POST"])
@login_required
def carpool_create():
    get_db().begin()
    try:
        get_db().query("INSERT INTO carpools (arrival_time, driver_id, car_description, concert) VALUES (:a, :b, :c, :d)", 
            a=request.form['arrival_time'], b=current_user.id, c=request.form['car_description'], d=request.form['concert'])
        car_id = next(iter(get_db().query("SELECT MAX(id) FROM carpools").next().items()))[1]
        get_db().query("INSERT INTO carpool_members (carpool_id, member_id) VALUES (:carpool_id, :member_id)", **{
            "carpool_id": car_id,
            "member_id": current_user.id
        })
        get_db().query("INSERT INTO chat_messages (carpool_id, user_id, content, time) VALUES (:carpool_id, :user_id, :content, :time)", **{
            "carpool_id": car_id,
            "user_id": current_user.id,
            "content": "I made this carpool!",
            "time": time.time()
        })  
        get_db().commit()
    except Exception as e:
        get_db().rollback()
        return abort(401, "Fail")
    
    with get_neo_db().session() as session:
      for record in session.run(
        "MERGE (p:Carpool {id:$car_id}) "
        "MERGE (c:Concert {id:$for_id}) "
        "MERGE (p)-[:FOR]->(c)",
        car_id=car_id,
        for_id=int(request.form['concert'])):
        pass
      for record in session.run(
        "MATCH (p:Carpool {id:$car_id})-[:FOR]->(c), (u:User {id:$user_id}) "
        "MERGE (u)-[:IN]->(p) "
        "MERGE (u)-[:LIKES]->(c)",
        car_id=car_id,
        user_id=current_user.id):
        pass
    return json.dumps({"id": car_id})

@app.route("/carpool/update", methods=["POST"])
@login_required
def carpool_update():
    lookup = get_db()["carpools"].find_one(id=request.form["id"], driver_id=current_user.id)
    if lookup is None:
        return abort(401, "Not owner of this carpool")
    get_db().begin()
    try:
        get_db().query("UPDATE carpools SET arrival_time=:arrival_time, driver_id=:driver_id, car_description=:car_description WHERE id=:id", **{
            "id": request.form["id"],
            "arrival_time": request.form['arrival_time'],
            "driver_id": current_user.id,
            "car_description": request.form['car_description']
        })
        get_db().commit()
    except:
        get_db().rollback()
        return abort(401, "Fail")
    return "Success"

@app.route("/carpool/list", methods=["GET"])
@login_required
def carpool_list():
    if request.args.get("id") is None:
        r = get_db().query("SELECT * FROM carpools AS p JOIN concerts c ON c.id=p.concert JOIN carpool_members AS m ON m.carpool_id=p.id WHERE m.member_id=:id ORDER BY c.name", id=current_user.id)
    else:
        r = get_db().query("SELECT * FROM carpools WHERE concert=:concert", concert=request.args.get("id"))
    return json.dumps([x for x in r])

@app.route("/carpool/suggest", methods=["GET"])
@login_required
def carpool_suggest():
    if request.args.get("id") is None:
        result = []
        with get_neo_db().session() as session:
          for r in session.run(
            "MATCH (u:User {id:$user_id}), (b:User) "
            "WHERE u <> b AND distance(b.location, u.location) < $radius "
            "WITH u, b "
            "MATCH (b)-[:IN]->(c) "
            "WHERE NOT (u)-[:IN]->(c) "
            "WITH DISTINCT u, c "
            "MATCH (b)-[:IN]->(c), (b)-[:LIKES]->(s)<-[:LIKES]-(u) "
            "WITH u, c, b, count(s) AS similarity_i "
            "WITH u, c, avg(similarity_i) AS similarity "
            "MATCH (b)-[:IN]->(c)-[:FOR]->(concert) "
            "RETURN c, similarity, min(distance(u.location, b.location)) AS dist, concert "
            "ORDER BY similarity DESC",
            radius=float(request.args.get("radius")),
            user_id=current_user.id):
            r2 = get_db().query("SELECT name FROM concerts WHERE id=:id", id=r["concert"].get("id"))
            result.append({
              "id": r["c"].get("id"),
              "similarity": r["similarity"],
              "name": r2.next()["name"],
              "dist": r["dist"]
            })
          return json.dumps(result)
    else:
        result = []
        with get_neo_db().session() as session:
          for r in session.run(
            "MATCH (u:User {id:$user_id}), (b)-[:IN]->(p)-[:FOR]->(c:Concert {id:$for_id}) "
            "WITH p, min(distance(u.location, b.location)) AS dist "
            "RETURN p, dist "
            "ORDER BY dist",
            for_id=int(request.args.get("id")),
            user_id=current_user.id):
            r2 = get_db().query("SELECT car_description FROM carpools WHERE id=:id", id=r["p"].get("id"))
            result.append({
              "id": r["p"].get("id"),
              "dist": r["dist"],
              "desc": r2.next()["car_description"]
            })
          return json.dumps(result)

@app.route("/carpool/get", methods=["GET"])
@login_required
def carpool_get():
    r = get_db().query("SELECT p.*, u.displayname, c.name, c.location FROM carpools AS p JOIN users AS u ON p.driver_id=u.id JOIN concerts AS c ON p.concert=c.id WHERE p.id=:id", id=request.args.get("id"))
    return json.dumps([x for x in r])

@app.route("/carpool/join", methods=["POST"])
@login_required
def carpool_join():
    lookup = get_db()["carpool_members"].find_one(carpool_id=request.form["id"], member_id=current_user.id)
    if lookup is not None:
        return abort(401, "Already in this carpool")
    get_db().begin()
    try:
        get_db().query("INSERT INTO carpool_members (carpool_id, member_id) VALUES (:carpool_id, :member_id)", **{
            "carpool_id": request.form["id"],
            "member_id": current_user.id
        })
        get_db().query("INSERT INTO chat_messages (carpool_id, user_id, content, time) VALUES (:carpool_id, :user_id, :content, :time)", **{
            "carpool_id": request.form["id"],
            "user_id": current_user.id,
            "content": "I joined this carpool!",
            "time": time.time()
        })       
        get_db().commit()
    except:
        get_db().rollback()
        return abort(401, "Fail")
    with get_neo_db().session() as session:
      for record in session.run(
        "MATCH (p:Carpool {id:$car_id})-[:FOR]->(c), (u:User {id:$user_id}) "
        "MERGE (u)-[:IN]->(p) "
        "MERGE (u)-[:LIKES]->(c)",
        car_id=int(request.form["id"]),
        user_id=current_user.id):
        pass
    return "Success"

@app.route("/carpool/like_concert", methods=["POST"])
@login_required
def carpool_like_concert():
    lookup = get_db()["concerts"].find_one(id=request.form["id"])
    if lookup is None:
        return abort(401, "No such concert")

    with get_neo_db().session() as session:
      for record in session.run("MATCH (u:User {id: $id}), (c:Concert {id:$concert_id}) MERGE (u)-[:LIKES]->(c)", id=current_user.id, concert_id=int(request.form["id"])):
        pass

    return "Success"

@app.route("/carpool/leave", methods=["POST"])
@login_required
def carpool_leave():
    delete_pool = False
    get_db().begin()
    try:
        get_db().query("DELETE FROM carpool_members WHERE member_id=:a AND carpool_id=:b", a=current_user.id, b=request.form["id"])
        get_db().query("INSERT INTO chat_messages (carpool_id, user_id, content, time) VALUES (:carpool_id, :user_id, :content, :time)", **{
            "carpool_id": request.form["id"],
            "user_id": current_user.id,
            "content": "I left this carpool!",
            "time": time.time()
        })  
        r = [x for x in get_db().query("SELECT * FROM carpool_members WHERE carpool_id=:id", id=request.form["id"])]
        if len(r) == 0:
            get_db().query("DELETE FROM carpools WHERE id=:a", a=request.form["id"])
            delete_pool = True
        else:
            r = get_db().query("SELECT driver_id FROM carpools WHERE id=:id", id=request.form["id"])
            driver_id = r.next()["driver_id"]
            r = get_db().query("SELECT member_id FROM carpool_members WHERE carpool_id=:id", id=request.form["id"])
            ids = [x["member_id"] for x in r]
            if driver_id not in ids:
                get_db().query("UPDATE carpools SET driver_id=:driver_id, car_description=:car_description WHERE id=:id", **{
                    "id": request.form["id"],
                    "driver_id": ids[0],
                    "car_description": "Previous driver has left"
                })
        get_db().commit()
    except Exception as e:
        print(str(e))
        get_db().rollback()
        return abort(401, "Fail")
    if delete_pool:
      with get_neo_db().session() as session:
        for record in session.run(
          "MATCH (p:Carpool {id:$car_id}) "
          "DETACH DELETE p",
          car_id=int(request.form["id"])):
          pass
    else:
      with get_neo_db().session() as session:
        for record in session.run(
          "MATCH (p:Carpool {id:$car_id}), (u:User {id:$user_id}), (u)-[r:IN]->(p)"
          "DELETE r",
          car_id=int(request.form["id"]),
          user_id=current_user.id):
          pass
    return "Success"

@app.route("/carpool/msg", methods=["POST"])
@login_required
def carpool_msg():
    lookup = get_db()["carpool_members"].find_one(carpool_id=request.form["id"], member_id=current_user.id)
    if lookup is None:
        return abort(401, "Fail")
    get_db().begin()
    try:
        get_db().query("INSERT INTO chat_messages (carpool_id, user_id, content, time) VALUES (:carpool_id, :user_id, :content, :time)", **{
            "carpool_id": request.form["id"],
            "user_id": current_user.id,
            "content": request.form["content"],
            "time": time.time()
        })
        get_db().commit()
    except:
        get_db().rollback()
        return abort(401, "Fail")
    return "Success"

@app.route("/carpool/get_msgs")
@login_required
def carpool_get_msgs():
    lookup = get_db()["carpool_members"].find_one(carpool_id=request.args.get("id"), member_id=current_user.id)
    if lookup is None:
        return abort(401, "Fail")
    r = get_db().query("SELECT u.id, u.displayname, m.content FROM chat_messages AS m JOIN users AS u ON m.user_id=u.id WHERE carpool_id = :id ORDER BY time", id=request.args.get("id"))
    return json.dumps([x for x in r])

@app.route("/carpool/demo1")
@login_required
def carpool_demo1():
    q = \
'''
SELECT y.genre,
(SELECT u.displayname FROM (SELECT p.driver_id AS id, count(*) AS ct
FROM carpools AS p
JOIN concerts AS c
ON p.concert=c.id
WHERE c.genre = y.genre
GROUP BY p.driver_id
ORDER BY ct
LIMIT 1) AS I JOIN users AS u on u.id=I.id) AS top_driver
FROM (SELECT DISTINCT genre FROM concerts) AS y
ORDER BY genre
'''
    r = get_db().query(q)
    return json.dumps([x for x in r])

@app.route("/carpool/demo2")
@login_required
def carpool_demo2():
    q = \
'''
SELECT venue, GROUP_CONCAT(artist) AS artists FROM (
SELECT a.artist, c.venue, count(*) AS ct
FROM concert_artists AS a
JOIN concerts AS c
ON a.concert = c.id
GROUP BY a.artist, c.venue
HAVING count(*) >= (SELECT MAX(ct2) FROM (
    SELECT count(*) AS ct2
    FROM concerts AS c2 
    JOIN concert_artists AS a2 
    ON c2.id=a2.concert 
    WHERE c2.venue = c.venue
    GROUP BY a2.artist
) AS x )
) AS y
GROUP BY venue
ORDER BY venue
'''
    r = get_db().query(q)
    return json.dumps([x for x in r])

@app.route("/carpool")
def carpool():
    return render_template("dashboard/carpools.html")

@app.route("/carpool_open")
def carpool_open():
    return render_template("dashboard/carpool_open.html")

@app.route("/carpool_choice")
def carpool_choice():
    return render_template("dashboard/carpool_choice.html")

@app.route("/suggested")
def suggested():
    return render_template("dashboard/suggested.html")

@app.route("/demo1")
def demo1():
    return render_template("dashboard/demo1.html")

@app.route("/demo2")
def demo2():
    return render_template("dashboard/demo2.html")