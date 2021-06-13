import logging
import gkeepapi
import json
from cryptography.fernet import Fernet
from flask import Flask, Response, request, jsonify
from feedgen.feed import FeedGenerator
from hashlib import sha256
import os

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

keep = gkeepapi.Keep()
logged_in = False

master_token = None

def sync(key):
    global logged_in
    global keep
    global master_token
    if logged_in:
        try:
            keep.sync()
            return
        except:
            pass
    if master_token is None:
        try:
            master_token = open("master.key", "rb").read()
        except:
            pass

    with open('credentials.json') as json_file:
        logged_in = False
        credentials = json.load(json_file)
        if key is None:
            key = open("secret.key", "rb").read()
        else:
            key = key.encode()
        password = Fernet(key).decrypt(
            credentials["password"].encode()).decode()
        user = credentials["user"]
        if master_token is None:
            keep.login(user, password)
            master_token = Fernet(key).encrypt(keep.getMasterToken().encode())
            with open("master.key", "wb") as token_file:
                token_file.write(master_token)
        else:
            try:
                keep.resume(user, Fernet(key).decrypt(master_token).decode())
            except:
                try:
                    os.remove("master.key")
                except:
                    pass
                return
        logged_in = True


@app.route("/pinned/notes")
def getPinnedNotes():
    result = {}
    result['notes'] = list(map(format, getNotes()))
    return jsonify(result)


@app.route("/pinned/notes.rss")
def getPinnedNotesRss():
    return getFeed(request.url).rss_str(pretty=True)


@app.route("/pinned/notes.atom")
def getPinnedNotesAtom():
    return getFeed(request.url).atom_str(pretty=True)


def getFeed(url):
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
    return fg

def getNotes():
    sync(request.args.get('key'))
    return keep.find(pinned=True)

def format(note):
    if note.title and note.title != "":
        return note.title
    else:
        return note.text.split('\n')[0]
