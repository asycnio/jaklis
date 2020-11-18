#!/usr/bin/env python3

import os, sys, requests, json, base58, base64
from userEnv import dunikey, pod
from natools import fmt, sign, get_privkey, box_decrypt
from datetime import datetime

rows = int(os.popen('stty size', 'r').read().split()[1])

#recipient = sys.argv[1]
recipient = get_privkey(dunikey, "pubsec").pubkey
nbrMsg = 5
boxType = "inbox"

def configDoc(recipient, nbrMsg):
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
                    "recipient": recipient
                }
            }
        }
    }
}
document = json.dumps(configDoc(recipient, nbrMsg))
# print(json.dumps(document))

headers = {
    'Content-type': 'application/json',
}
msgJSON = requests.post('{0}/message/{1}/_search'.format(pod, boxType), headers=headers, data=document).json()["hits"]

total = msgJSON["total"]
for hits in msgJSON["hits"]:
    isMsg = hits["_id"]
    msgSrc = hits["_source"]
    issuer = msgSrc["issuer"]
    nonce = msgSrc["nonce"]
    nonce = base58.b58decode(nonce)
    title = base64.b64decode(msgSrc["title"])
    title = box_decrypt(title, get_privkey(dunikey, "pubsec"), issuer, nonce).decode()
    content = base64.b64decode(msgSrc["content"])
    content = box_decrypt(content, get_privkey(dunikey, "pubsec"), issuer, nonce).decode()

    date = datetime.fromtimestamp(msgSrc["time"]).strftime(", le %d/%m/%Y à %H:%M  ")

    headerMsg = "  De " + issuer + date
    print('-'.center(rows, '-'))
    print(headerMsg.center(rows, '-'))
    print('-'.center(rows, '-'))
    print("Objet: " + title)
    print(content)