from flask import Blueprint, Response, abort, redirect, render_template, request
from flask_login import login_required, login_user, logout_user, current_user
from urllib.parse import urlparse, urljoin
from utils import get_db, get_user, get_neo_db
import hashlib
import os
import base64
import json

app = Blueprint('accounts', __name__, template_folder='templates')

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

def generate_salt():
    salt = os.urandom(16)
    return base64.b64encode(salt).decode("ascii")


@app.route("/conditions")
def conditions():
    return render_template("accounts/conditions.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']
        lookup = get_db()["users"].find_one(username=username)
        if lookup is None:
            return abort(401, "Login failed")
        m = hashlib.sha256()
        m.update((lookup["salt"] + password).encode('utf-8'))
        hash = m.hexdigest()
        lookup = get_db()["users"].find_one(username=username, password=hash)
        if lookup is None:
            return abort(401, "Login failed")
        user = get_user(lookup["id"])
        login_user(user, remember=True)
        next = request.args.get("next")
        if next is None or not is_safe_url(next):
            next = "/"
        return redirect(next)
    else:
        return render_template("accounts/login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']
        salt = generate_salt()
        m = hashlib.sha256()
        m.update((salt + password).encode('utf-8'))
        hash = m.hexdigest()
        get_db().begin()
        try:
            get_db()["users"].insert({
                "username": username,
                "password": hash,
                "salt": salt,
                "displayname": username,
                "permissions": 2
            })
            get_db().commit()
        except:
            get_db().rollback()
            abort(401, "Registration error")
        lookup = get_db()["users"].find_one(username=username, password=hash)
        user = get_user(lookup["id"])
        login_user(user, remember=True)
        next = request.args.get("next")
        if next is None or not is_safe_url(next):
            next = "/"
        return redirect(next)
    else:
        return render_template("accounts/register.html")

@app.route("/update_account", methods=["GET", "POST"])
@login_required
def update_account():
    if request.method == 'POST':
        password = request.form['password']
        lookup = get_db()["users"].find_one(id=current_user.id)
        m = hashlib.sha256()
        m.update((lookup["salt"] + password).encode('utf-8'))
        hash = m.hexdigest()
        lookup = get_db()["users"].find_one(id=current_user.id, password=hash)
        if lookup is None:
            return abort(401, "Wrong current password")
        displayname = request.form['displayname']
        new_password = request.form['newpassword']
        change = {
            "id": current_user.id,
            "displayname": displayname
        }
        if new_password != "":
            salt = generate_salt()
            m = hashlib.sha256()
            m.update((salt + new_password).encode('utf-8'))
            hash = m.hexdigest()
            change["password"] = hash
            change["salt"] = salt
        get_db().begin()
        try:
            get_db()["users"].update(change, ["id"])
            get_db().commit()
        except:
            get_db().rollback()
            abort(401, "Registration error")
        user = get_user(current_user.id)
        login_user(user, remember=True)

        longitude = float(request.form['longitude'])
        latitude = float(request.form['latitude'])

        if longitude != 0.0 or latitude != 0.0:
            with get_neo_db().session() as session:
                for record in session.run(
                    "MERGE (u:User {id: $id}) SET u.location=point({longitude:$longitude, latitude:$latitude})", 
                    id=current_user.id, 
                    longitude=float(request.form['longitude']), 
                    latitude=float(request.form['latitude'])):
                    pass
        return redirect("/update_account")
    else:
        return render_template("dashboard/update_account.html")

@app.route("/get_location")
@login_required
def get_location():
    latitude = 0.0
    longitude = 0.0
    try:
        with get_neo_db().session() as session:
            for record in session.run(
                "MATCH (u:User {id: $id}) RETURN u.location", 
                id=current_user.id):
                latitude = record["u.location"].latitude
                longitude = record["u.location"].longitude
    except:
        pass
    return json.dumps({"latitude": latitude, "longitude": longitude})

@app.route("/logout")
def logout():
    logout_user()
    return Response('<script>window.location="/"</script>')