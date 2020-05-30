"""Basics of a Bottle web server

Gary Bishop May 2020
"""

import bottle
from bottle import view
from db import with_db, insert
import json
import os.path as osp
from datetime import datetime


# startup bottle
# allow returning datetime objects in json
app = application = bottle.Bottle(autojson=False)
app.install(bottle.JSONPlugin(json_dumps=lambda s: json.dumps(s, default=str)))


# make get_url available in all templates
def get_url(name, user=None, **kwargs):
    """get_url for use from templates"""
    url = app.get_url(name, **kwargs)
    return url


bottle.SimpleTemplate.defaults["get_url"] = get_url


def allow_json(func):
    """ Decorator: renders as json if requested """

    def wrapper(*args, **kwargs):
        """wrapper"""
        result = func(*args, **kwargs)
        if "application/json" in bottle.request.headers.get(
            "Accept", ""
        ) and isinstance(result, dict):
            return bottle.HTTPResponse(result)
        return result

    return wrapper


def cors(func):
    """Allow cross origin requests"""

    def wrapper(*args, **kwargs):
        bottle.response.set_header("Access-Control-Allow-Origin", "*")
        bottle.response.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        bottle.response.set_header(
            "Access-Control-Allow-Headers", "Origin, Content-Type"
        )

        # skip the function if it is not needed
        if bottle.request.method == "OPTIONS":
            return

        return func(*args, **kwargs)

    return wrapper


def static(filename):
    """
    Produce the path to a static file
    """
    p = osp.join("./static", filename)
    m = osp.getmtime(p)
    s = "%x" % int(m)
    u = app.get_url("static", filename=filename)
    return u + "?" + s


bottle.SimpleTemplate.defaults["static"] = static


@app.route("/static/<filename:path>", name="static")
def serveStatic(filename):
    """
    Serve static files in development
    """
    kwargs = {"root": "./static"}
    return bottle.static_file(filename, **kwargs)


@app.route("/", name="root")
def root():
    """Example root page"""
    return ""


@app.route("/drop", name="drop")
@cors
@view("list")
@allow_json
@with_db
def listdrops(db):
    """List the drops"""
    drops = db.execute("""select id, time from drops where deleted != 1""").fetchall()
    return {"drops": drops}


@app.route("/drop/<id>", name="get")
@cors
@with_db
def get(id, db):
    """Return the json from a drop"""
    row = db.execute("""select json from drops where id = ?""", [id]).fetchone()
    if row:
        return json.loads(row["json"])
    else:
        return bottle.HTTPError(404, "No such drop")


@app.route("/drop/<id>", name="delete", method="DELETE")
@cors
@with_db
def delete(id, db):
    """Delete the drop"""
    db.execute("""update drops set deleted=1 where id = ?""", [id]).fetchone()
    return {"deleted": id}


@app.route("/drop", name="post", method="POST")
@cors
@with_db
def post(db):
    """Add a drop"""
    data = bottle.request.json
    cursor = insert(db, "drops", time=datetime.now(), json=json.dumps(data), deleted=0)
    return {"id": cursor.lastrowid}


class StripPathMiddleware:
    """
    Get that slash out of the request
    """

    def __init__(self, a):
        self.a = a

    def __call__(self, e, h):
        e["PATH_INFO"] = e["PATH_INFO"].rstrip("/")
        return self.a(e, h)


def serve(test=True):
    """Run the server for testing"""
    from livereload import Server

    global Testing
    Testing = test

    bottle.debug(True)
    server = Server(StripPathMiddleware(app))
    server.serve(port=8080, host="0.0.0.0")


if __name__ == "__main__":
    serve()
