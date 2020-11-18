#!/usr/bin/env python3

import os, sys, requests, json, base58, base64
from natools import fmt, sign, get_privkey, box_decrypt
from datetime import datetime
from termcolor import colored


class ReadCesium:
    def __init__(self, dunikey, pod):
        # Get my pubkey from my private key
        try:
            self.dunikey = dunikey
        except:
            sys.stderr.write("Please fill the path to your private key (PubSec)\n")
            sys.exit(1)

        self.recipient = get_privkey(dunikey, "pubsec").pubkey
        self.pod = pod

    # Configure JSON document to send
    def configDoc(self, nbrMsg, outbox):
        if outbox:
            boxType = "issuer"
        else:
            boxType = "recipient"

        return {
        "sort": { "time": "desc" },
        "from": 0,
        "size": nbrMsg,
        "_source":[
            "issuer",
            "recipient",
            "title",
            "content",
            "time",
            "nonce",
            "read_signature"
        ],"query":{
            "bool":{
                "filter":{
                    "term":{
                        boxType: self.recipient
                    }
                }
            }
            }
        }


    def sendDocument(self, nbrMsg, outbox):
        if outbox:
            boxType = "outbox"
        else:
            boxType = "inbox"

        document = json.dumps(self.configDoc(nbrMsg, outbox))
        headers = {
            'Content-type': 'application/json',
        }

        # Send JSON document and get JSON result
        brut = requests.post('{0}/message/{1}/_search'.format(self.pod, boxType), headers=headers, data=document).json()["hits"]
        return brut

    # Parse JSON result and display messages
    def readMessages(self, msgJSON):
        # Get terminal size
        rows = int(os.popen('stty size', 'r').read().split()[1])

        self.total = msgJSON["total"]
        infoTotal = "  Nombre de messages: " + str(self.total) + "  "
        print(colored(infoTotal.center(rows, '#'), "yellow"))
        for hits in msgJSON["hits"]:
            self.idMsg = hits["_id"]
            msgSrc = hits["_source"]
            self.issuer = msgSrc["issuer"]
            nonce = msgSrc["nonce"]
            nonce = base58.b58decode(nonce)
            self.title = base64.b64decode(msgSrc["title"])
            self.title = box_decrypt(self.title, get_privkey(self.dunikey, "pubsec"), self.issuer, nonce).decode()
            self.content = base64.b64decode(msgSrc["content"])
            self.content = box_decrypt(self.content, get_privkey(self.dunikey, "pubsec"), self.issuer, nonce).decode()
            self.dateS = msgSrc["time"]
            date = datetime.fromtimestamp(self.dateS).strftime(", le %d/%m/%Y à %H:%M  ")
            headerMsg = "  De " + self.issuer + date + "(ID: {})".format(self.idMsg) + "  "

            print('-'.center(rows, '-'))
            print(colored(headerMsg, "blue").center(rows+9, '-'))
            print('-'.center(rows, '-'))
            print("Objet: " + self.title)
            print(self.content)


    def read(self, nbrMsg, outbox):
        jsonMsg = self.sendDocument(nbrMsg, outbox)
        self.readMessages(jsonMsg)

