from flask import g, jsonify
from flask_login import UserMixin
import dataset
import time
import threading
import json
import os
from neo4j import GraphDatabase

lock = threading.RLock()
# used in server.py
newsfeed_paths = ["/", "/index.html", "/newsfeed"]
navigation = [
    {"name": "Concerts", "path": newsfeed_paths, "icon": "fa fa-fw fa-rss", "active": False},
    {"name": "Carpools", "path": ["/carpool"], "icon": "fa fa-fw fa-car", "active": False},
    {"name": "Suggested", "path": ["/suggested"], "icon": "fa fa-fw fa-music", "active": False},
    #{"name": "Demo 1", "path": ["/demo1"], "icon": "fa fa-fw fa-info", "active": False},
    #{"name": "Demo 2", "path": ["/demo2"], "icon": "fa fa-fw fa-info", "active": False},
    {"name": "Settings", "path": ["/update_account"], "icon": "fa fa-fw fa-cog", "active": False},
    {"name": "Terms & Conditions", "path": ["javascript:window.open('/conditions', '_blank')"], "icon": "fa fa-fw fa-exclamation-triangle", "active": False},
    {"name": "Logout", "path": ["/logout"], "icon": "fa fa-fw fa-power-off", "active": False}
]
db = None
neo_db = None

class User(UserMixin):
    def __init__(self, id, username, displayname, permissions):
        self.id = id
        self.username = username
        self.displayname = displayname
        self.permissions = permissions
    
    def as_dict(self):
        return dict(id=self.id, username=self.username, displayname=self.displayname, permissions=self.permissions)
    
    def __repr__(self):
        return "%d/%s" % (self.id, self.name)

def get_db():
    global db
    if db is None:
        args = {}
        if "sqlite" in os.environ.get("DATABASE_URL"):
            args["check_same_thread"] = False
        db = dataset.connect(os.environ.get("DATABASE_URL"), engine_kwargs={"poolclass": None, "connect_args":args})
    return db

def get_neo_db():
    global neo_db
    if neo_db is None:
        neo_db = GraphDatabase.driver(os.environ.get("GRAPHENEDB_BOLT_URL"), auth=(os.environ.get("GRAPHENEDB_BOLT_USER"), os.environ.get("GRAPHENEDB_BOLT_PASSWORD")))
    return neo_db

def get_user(userid):
    userid = int(userid)
    lookup = get_db()["users"].find_one(id=userid)
    if lookup is None:
        return None
    user = User(userid, lookup["username"], lookup["displayname"], lookup["permissions"])
    return user

def get_time():
    return int(time.time())

def get_navigation(path):
    res = []
    for n in navigation:
        if path in n["path"]:
            new_n = n.copy()
            new_n["active"] = True
            res.append(new_n)
        else:
            res.append(n)
    return res