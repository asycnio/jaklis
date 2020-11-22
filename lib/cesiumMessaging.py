#!/usr/bin/env python3

import os, sys, ast, requests, json, base58, base64, time, string, random, re
from natools import fmt, sign, get_privkey, box_decrypt, box_encrypt
from hashlib import sha256
from datetime import datetime
from termcolor import colored

VERSION = "0.1-dev"
PUBKEY_REGEX = "(?![OIl])[1-9A-Za-z]{42,45}"

def pp_json(json_thing, sort=True, indents=4):
    if type(json_thing) is str:
        print(json.dumps(json.loads(json_thing), sort_keys=sort, indent=indents))
    else:
        print(json.dumps(json_thing, sort_keys=sort, indent=indents))
    return None

class ReadFromCesium:
    def __init__(self, dunikey, pod):
        # Get my pubkey from my private key
        try:
            self.dunikey = dunikey
            if not dunikey:
                raise ValueError("Dunikey is empty")
        except:
            sys.stderr.write("Please fill the path to your private key (PubSec)\n")
            sys.exit(1)

        self.recipient = get_privkey(dunikey, "pubsec").pubkey
        self.pod = pod

        if not re.match(PUBKEY_REGEX, self.recipient) or len(self.recipient) > 45:
            sys.stderr.write("La clé publique n'est pas au bon format.\n")
            sys.exit(1)

    # Configure JSON document to send
    def configDoc(self, nbrMsg, outbox):
        if outbox:
            boxType = "issuer"
        else:
            boxType = "recipient"

        data = {}
        data['sort'] = { "time": "desc" }
        data['from'] = 0
        data['size'] = nbrMsg
        data['_source'] = ['issuer','recipient','title','content','time','nonce','read_signature']
        data['query'] = {}
        data['query']['bool'] = {}
        data['query']['bool']['filter'] = {}
        data['query']['bool']['filter']['term'] = {}
        data['query']['bool']['filter']['term'][boxType] = self.recipient

        document = json.dumps(data)
        return document

    def sendDocument(self, nbrMsg, outbox):
        if outbox:
            boxType = "outbox"
        else:
            boxType = "inbox"

        document = self.configDoc(nbrMsg, outbox)
        headers = {
            'Content-type': 'application/json',
        }

        # Send JSON document and get JSON result
        result = requests.post('{0}/message/{1}/_search'.format(self.pod, boxType), headers=headers, data=document)
        if result.status_code == 200:
            return result.json()["hits"]
        else:
            sys.stderr.write("Echec de l'envoi du document de lecture des messages...\n" + result.text)

    # Parse JSON result and display messages
    def readMessages(self, msgJSON, nbrMsg, outbox):
        def decrypt(msg):
            msg64 = base64.b64decode(msg)
            return box_decrypt(msg64, get_privkey(self.dunikey, "pubsec"), self.issuer, nonce).decode()

        # Get terminal size
        rows = int(os.popen('stty size', 'r').read().split()[1])

        totalMsg = msgJSON["total"]
        if nbrMsg > totalMsg:
            nbrMsg = totalMsg

        if totalMsg == 0:
            print(colored("Aucun message à afficher.", 'yellow'))
            return True
        else:
            infoTotal = "  Nombre de messages: " + str(nbrMsg) + "/" + str(totalMsg) + "  "
            print(colored(infoTotal.center(rows, '#'), "yellow"))
            for hits in msgJSON["hits"]:
                self.idMsg = hits["_id"]
                msgSrc = hits["_source"]
                self.issuer = msgSrc["issuer"]
                nonce = msgSrc["nonce"]
                nonce = base58.b58decode(nonce)
                self.dateS = msgSrc["time"]
                date = datetime.fromtimestamp(self.dateS).strftime(", le %d/%m/%Y à %H:%M  ")
                if outbox:
                    startHeader = "  À " + msgSrc["recipient"]
                else:
                    startHeader = "  De " + self.issuer
                headerMsg = startHeader + date + "(ID: {})".format(self.idMsg) + "  "

                print('-'.center(rows, '-'))
                print(colored(headerMsg, "blue").center(rows+9, '-'))
                print('-'.center(rows, '-'))
                try:
                    self.title = decrypt(msgSrc["title"])
                    self.content = decrypt(msgSrc["content"])
                except Exception as e:
                    sys.stderr.write(colored(str(e), 'red') + '\n')
                    pp_json(hits)
                    continue
                print("Objet: " + self.title)
                print(self.content)
                # pp_json(hits)


    def read(self, nbrMsg, outbox):
        jsonMsg = self.sendDocument(nbrMsg, outbox)
        self.readMessages(jsonMsg, nbrMsg, outbox)




#################### Sending class ####################




class SendToCesium:
    def __init__(self, dunikey, pod, recipient, outbox):
        # Get my pubkey from my private key
        try:
            self.dunikey = dunikey
            if not dunikey:
                raise ValueError("Dunikey is empty")
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

        if not re.match(PUBKEY_REGEX, recipient) or len(recipient) > 45:
            sys.stderr.write("La clé publique n'est pas au bon format.\n")
            sys.exit(1)


    def encryptMsg(self, msg):
        return fmt["64"](box_encrypt(msg.encode(), get_privkey(self.dunikey, "pubsec"), self.recipient, self.nonce)).decode()

    def configDoc(self, title, msg):
        b58nonce = base58.b58encode(self.nonce).decode()

        # Get current timestamp
        timeSent = int(time.time())

        # Generate custom JSON
        data = {}
        data['issuer'] = self.issuer
        data['recipient'] = self.recipient
        data['title'] = title
        data['content'] = msg
        data['time'] = timeSent
        data['nonce'] = b58nonce
        data['version'] = 2
        document = json.dumps(data)

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
            if result.status_code == 200:
                print(colored("Message envoyé avec succès !", "green"))
                print("ID: " + result.text)
                return result
            else:
                sys.stderr.write("Erreur inconnue:" + '\n')
                print(str(pp_json(result.text)) + '\n')

    def send(self, title, msg):
        finalDoc = self.configDoc(self.encryptMsg(title), self.encryptMsg(msg))     # Configure JSON document to send
        self.sendDocument(finalDoc)                                                 # Send final signed document




#################### Deleting class ####################




class DeleteFromCesium:
    def __init__(self, dunikey, pod, outbox):
        # Get my pubkey from my private key
        try:
            self.dunikey = dunikey
            if not dunikey:
                raise ValueError("Dunikey is empty")
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

        #document = str({"version":2,"index":"message","type":boxType,"id":idMsg,"issuer":self.issuer,"time":timeSent}).replace("'",'"')
        data = {}
        data['version'] = 2
        data['index'] = "message"
        data['type'] = boxType
        data['id'] = idMsg
        data['issuer'] = self.issuer
        data['time'] = timeSent
        document = json.dumps(data)

        # Generate hash of document
        hashDoc = sha256(document.encode()).hexdigest().upper()

        # Generate signature of document
        signature = fmt["64"](sign(hashDoc.encode(), get_privkey(self.dunikey, "pubsec"))[:-len(hashDoc.encode())]).decode()

        # Build final document
        data = {}
        data['hash'] = hashDoc
        data['signature'] = signature
        signJSON = json.dumps(data)
        finalJSON = {**json.loads(signJSON), **json.loads(document)}
        finalDoc = json.dumps(finalJSON)

        return finalDoc

    def sendDocument(self, document, idMsg):
        headers = {
            'Content-type': 'application/json',
        }

        # Send JSON document and get result
        try:
            result = requests.post('{0}/history/delete'.format(self.pod), headers=headers, data=document)
            if result.status_code == 404:
                raise ValueError("Message introuvable")
            elif result.status_code == 403:
                raise ValueError("Vous n'êtes pas l'auteur de ce message.")
        except Exception as e:
            sys.stderr.write(colored("Impossible de supprimer le message {0}:\n".format(idMsg), 'red') + str(e) + "\n")
            return False
        else:
            if result.status_code == 200:
                print(colored("Message {0} supprimé avec succès !".format(idMsg), "green"))
                return result
            else:
                sys.stderr.write("Erreur inconnue.")

    def delete(self, idsMsgList):
        for idMsg in idsMsgList:
            finalDoc = self.configDoc(idMsg)
            self.sendDocument(finalDoc, idMsg)

