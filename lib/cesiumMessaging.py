#!/usr/bin/env python3

import os, sys, ast, requests, json, base58, base64, time, string, random, re
from natools import fmt, sign, get_privkey, box_decrypt, box_encrypt
from hashlib import sha256
from datetime import datetime
from termcolor import colored


class ReadFromCesium:
    def __init__(self, dunikey, pod):
        # Get my pubkey from my private key
        try:
            self.dunikey = dunikey
            if dunikey == "":
                raise ValueError("Dunikey is empty")
        except:
            sys.stderr.write("Please fill the path to your private key (PubSec)\n")
            sys.exit(1)

        self.recipient = get_privkey(dunikey, "pubsec").pubkey
        self.pod = pod

        if not re.match(r"(?![OIl])[1-9A-Za-z]{42,45}", self.recipient):
            sys.stderr.write("La clé publique n'est pas au bon format.\n")
            sys.exit(1)

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
        result = requests.post('{0}/message/{1}/_search'.format(self.pod, boxType), headers=headers, data=document).json()["hits"]
        return result

    # Parse JSON result and display messages
    def readMessages(self, msgJSON, nbrMsg):
        # Get terminal size
        rows = int(os.popen('stty size', 'r').read().split()[1])

        self.total = msgJSON["total"]
        infoTotal = "  Nombre de messages: " + str(nbrMsg) + "/" + str(self.total) + "  "
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
        self.readMessages(jsonMsg, nbrMsg)




#################### Sending class ####################




class SendToCesium:
    def __init__(self, dunikey, pod, recipient, outbox):
        # Get my pubkey from my private key
        try:
            self.dunikey = dunikey
        except:
            sys.stderr.write("Please fill the path to your private key (PubSec)\n")
            sys.exit(1)

        self.issuer = get_privkey(dunikey, "pubsec").pubkey
        self.pod = pod
        self.recipient = recipient
        self.outbox = outbox

        # Generate pseudo-random nonce
        nonce=[]
        for i in range(32):
            nonce.append(random.choice(string.ascii_letters + string.digits))
        self.nonce = base64.b64decode(''.join(nonce))

        if not re.match(r"(?![OIl])[1-9A-Za-z]{42,45}", recipient):
            sys.stderr.write("La clé publique n'est pas au bon format.\n")
            sys.exit(1)


    def encryptMsg(self, msg):
        return fmt["64"](box_encrypt(msg.encode(), get_privkey(self.dunikey, "pubsec"), self.issuer, self.nonce)).decode()

    def configDoc(self, title, msg):
        b58nonce = base58.b58encode(self.nonce).decode()

        # Get current timestamp
        timeSent = int(time.time())

        # Generate document to customize
        document = str({"issuer":self.issuer,"recipient":self.recipient,"title":title,"content":msg,"time":timeSent,"nonce":b58nonce,"version":2}).replace("'",'"')

        # Generate hash of document
        hashDoc = sha256(document.encode()).hexdigest().upper()

        # Generate signature of document
        signature = fmt["64"](sign(hashDoc.encode(), get_privkey(self.dunikey, "pubsec"))[:-len(hashDoc.encode())]).decode()

        # Build final document
        finalDoc = '{' + '"hash":"{0}","signature":"{1}",'.format(hashDoc, signature) + document[1:]

        return finalDoc


    def sendDocument(self, document):
        if self.outbox:
            boxType = "outbox"
        else:
            boxType = "inbox"

        headers = {
            'Content-type': 'application/json',
        }

        # Send JSON document and get result
        try:
            result = requests.post('{0}/message/{1}?pubkey={2}'.format(self.pod, boxType, self.recipient), headers=headers, data=document)
        except Exception as e:
            sys.stderr.write("Impossible d'envoyer le message:\n" + str(e))
            sys.exit(1)
        else:
            print(colored("Message envoyé avec succès !", "green"))
            print("ID: " + result.text)
            return result


    def send(self, title, msg):
        finalDoc = self.configDoc(self.encryptMsg(title), self.encryptMsg(msg))     # Configure JSON document to send
        self.sendDocument(finalDoc)                                                 # Send final signed document




#################### Deleting class ####################




class DeleteFromCesium:
    def __init__(self, dunikey, pod, outbox):
        # Get my pubkey from my private key
        try:
            self.dunikey = dunikey
        except:
            sys.stderr.write("Please fill the path to your private key (PubSec)\n")
            sys.exit(1)

        self.issuer = get_privkey(dunikey, "pubsec").pubkey
        self.pod = pod
        self.outbox = outbox


    def configDoc(self, idMsg):
        # Get current timestamp
        timeSent = int(time.time())

        # Generate document to customize

        if self.outbox:
            boxType = "outbox"
        else:
            boxType = "inbox"

        document = str({"version":2,"index":"message","type":boxType,"id":idMsg,"issuer":self.issuer,"time":timeSent}).replace("'",'"')
        # "{\"version\":2,\"index\":\"message\",\"type\":\"$type\",\"id\":\"$id\",\"issuer\":\"$issuer\",\"time\":$times}"

        # Generate hash of document
        hashDoc = sha256(document.encode()).hexdigest().upper()

        # Generate signature of document
        signature = fmt["64"](sign(hashDoc.encode(), get_privkey(self.dunikey, "pubsec"))[:-len(hashDoc.encode())]).decode()

        # Build final document
        finalDoc = '{' + '"hash":"{0}","signature":"{1}",'.format(hashDoc, signature) + document[1:]

        return finalDoc

    def sendDocument(self, document):
        headers = {
            'Content-type': 'application/json',
        }

        # Send JSON document and get result
        try:
            result = requests.post('{0}/history/delete'.format(self.pod), headers=headers, data=document)
            if result.status_code == 404:
                raise ValueError("Message introuvable")
        except Exception as e:
            sys.stderr.write("Impossible de supprimer le message:\n" + str(e) + "\n")
            sys.exit(1)
        else:
            print(colored("Message supprimé avec succès !", "green"))
            return result

    def delete(self, idMsg):
        finalDoc = self.configDoc(idMsg)
        self.sendDocument(finalDoc)

