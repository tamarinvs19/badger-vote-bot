import os


try:
    TOKEN = os.environ['TG_TOKEN']
except KeyError:
    with open('token', 'r') as fout:
        TOKEN = fout.readline().strip()

PORT = int(os.environ.get('PORT', 8443))
APPNAME = 'badger-vote-bot'
