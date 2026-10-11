import logging
import gkeepapi
from cryptography.fernet import Fernet
from flask import Flask, Response, request, jsonify
from feedgen.feed import FeedGenerator
import os

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

keep = gkeepapi.Keep()
logged_in = False


def required_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def sync():
    global logged_in
    global keep
    if logged_in:
        try:
            keep.sync()
            return
        except:
            pass
    logged_in = False
    email = required_env("EMAIL")
    key = required_env("SECRET_KEY").encode()
    master_token = Fernet(key).decrypt(
        required_env("MASTER_KEY").encode()).decode()
    keep.resume(email, master_token)
    logged_in = True


@app.route("/pinned/notes")
def getPinnedNotes():
    result = {}
    result['notes'] = list(map(format, getNotes()))
    return jsonify(result)


@app.route("/pinned/notes.rss")
def getPinnedNotesRss():
    return getFeed(request.url, placeholderRequested(request)).rss_str(pretty=True)


@app.route("/pinned/notes.atom")
def getPinnedNotesAtom():
    return getFeed(request.url, placeholderRequested(request)).atom_str(pretty=True)

def placeholderRequested(request):
    return "empty" in request.args and request.args["empty"] == "placeholder"

def getFeed(url, emptyPlaceholder=False):
    fg = FeedGenerator()
    fg.id(url)
    fg.link(href=url, rel='self')
    fg.link(href='https://keep.google.com/u/0/?pli=1#home', rel='alternate')
    fg.title('Notes')
    fg.description('Do not forget')
    for note in getNotes():
        fe = fg.add_entry()
        fe.id("https://keep.google.com/u/0/#NOTE/"+note.id)
        fe.link(href='https://keep.google.com/u/0/#NOTE/'+note.id, rel='alternate')
        fe.title(format(note))
    if emptyPlaceholder:
        fe = fg.add_entry()
        fe.id("https://keep.google.com")
        fe.link(href='https://keep.google.com', rel='alternate')
        fe.title(" ")
    return fg

def getNotes():
    sync()
    return keep.find(pinned=True)

def format(note):
    if note.title and note.title != "":
        return note.title
    else:
        return note.text.split('\n')[0]


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
