from flask import Flask, Response, render_template, request
from flask_login import LoginManager, login_required, current_user
from utils import get_user, get_navigation, User, get_time, newsfeed_paths
from permissions import get_members
import threading
import time
from werkzeug.serving import is_running_from_reloader
from htmlmin.main import minify
import os

# Change this instead of the debug below!
debug = True

app = Flask(__name__, static_url_path='/static')

app.config.update(
    SECRET_KEY=b'\xfa\x08\x86/\xe3\xef\xfeb\x11\xbd\x80\xc3\xa9>]b'
)

import blueprints.accounts.views as accounts_views
import blueprints.dashboard.views as dashboard_views
import blueprints.carpool.views as carpool_views
app.register_blueprint(accounts_views.app)
app.register_blueprint(dashboard_views.app)
app.register_blueprint(carpool_views.app)

# Seconds to update cached data
UPDATE_TIME = 2

staticCache = {
    "members": get_members()
}
dataLock = threading.Lock()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "accounts.login"

@login_manager.user_loader
def load_user(userid):
    return get_user(userid)

@app.route("/")
@app.route("/index.html")
@app.route("/newsfeed")
@login_required
def home():
    return render_template("dashboard/newsfeed.html")

@app.errorhandler(404)
@login_required
def page_not_found(e):
    return render_template("dashboard/404.html")

@app.errorhandler(401)
def unauthorized(e):
    return Response(e.description, 401)

@app.context_processor
def navigation():
    return dict(navigation=get_navigation(request.path))

def background_job():
    global staticCache
    while True:
        members = get_members()
        with dataLock:
            staticCache["members"] = members
        time.sleep(UPDATE_TIME)

@app.context_processor
def userdata():
    with dataLock:
        return dict(userdata={
        })

@app.context_processor
def members():
    with dataLock:
        return dict(members=staticCache["members"])

@app.after_request
def response_minify(response):
    if debug:
        return response
    """
    minify html response to decrease site traffic
    """
    if response.content_type == u'text/html; charset=utf-8':
        response.set_data(
            minify(response.get_data(as_text=True), remove_comments=True, remove_empty_space=True, remove_all_empty_space=True, reduce_empty_attributes=True, reduce_boolean_attributes=False, remove_optional_attribute_quotes=True, convert_charrefs=False)
        )
        return response
    return response

# start thread in the correct process
# (when debugging we want to reload with the child)
# https://stackoverflow.com/questions/25504149/why-does-running-the-flask-dev-server-run-itself-twice
if is_running_from_reloader() == debug:
    threading.Thread(target=background_job, daemon=True).start()

# Do not change debug here!
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get("PORT"), debug=debug, threaded=True)
