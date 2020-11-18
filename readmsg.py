#!/usr/bin/env python3

import os, sys, requests, json, base58, base64
from userEnv import dunikey, pod
from natools import fmt, sign, get_privkey
from datetime import datetime

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
    title = msgSrc["title"]
    content = msgSrc["content"]
    nonce = msgSrc["nonce"]
    date = datetime.fromtimestamp(msgSrc["time"]).strftime("Le %d/%m/%Y à %H:%M")


    print("----------")
    print(date)
    print("Objet: " + title)
    print("Message: " + content)



