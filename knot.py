import logging
import gkeepapi
import json
from cryptography.fernet import Fernet
from flask import Flask, Response, request, jsonify
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
                os.remove("master.key")
                return
        logged_in = True


@app.route("/pinned/notes")
def status():
    sync(request.args.get('key'))
    notes = []
    for note in keep.find(pinned=True):
        if note.title and note.title != "":
            notes.append(note.title)
        else:
            notes.append(note.text.split('\n')[0])
    result = {}
    result['notes'] = notes
    return jsonify(result)
