import gkeepapi
import json
from cryptography.fernet import Fernet

keep = gkeepapi.Keep()

def login(key):
    with open('credentials.json') as json_file:
        credentials = json.load(json_file)
        if not key:
            key = open("secret.key", "rb").read()
        password = Fernet(open("secret.key", "rb").read()).decrypt(
            credentials["password"].encode()).decode()
        user = credentials["user"]

login(None)

