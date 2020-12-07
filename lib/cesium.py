import os, sys, ast, requests, json, base58, base64, time, string, random, re
from lib.natools import fmt, sign, get_privkey, box_decrypt, box_encrypt
from time import sleep
from hashlib import sha256
from datetime import datetime
from termcolor import colored

PUBKEY_REGEX = "(?![OIl])[1-9A-Za-z]{42,45}"

def pp_json(json_thing, sort=True, indents=4):
    # Print beautifull JSON
    if type(json_thing) is str:
        print(json.dumps(json.loads(json_thing), sort_keys=sort, indent=indents))
    else:
        print(json.dumps(json_thing, sort_keys=sort, indent=indents))
    return None

class CesiumPlus:
    def __init__(self, dunikey, pod):
        # Get my pubkey from my private key
        try:
            self.dunikey = dunikey
            if not dunikey:
                raise ValueError("Dunikey is empty")
        except:
            sys.stderr.write("Please fill the path to your private key (PubSec)\n")
            sys.exit(1)

        self.pubkey = get_privkey(dunikey, "pubsec").pubkey
        self.pod = pod

        if not re.match(PUBKEY_REGEX, self.pubkey) or len(self.pubkey) > 45:
            sys.stderr.write("La clé publique n'est pas au bon format.\n")
            sys.exit(1)

    def signDoc(self, document):
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

    def read(self, nbrMsg, outbox, isJSON):
        readCesium = ReadFromCesium(self.dunikey,  self.pod)
        jsonMsg = readCesium.sendDocument(nbrMsg, outbox)
        if isJSON:
            jsonFormat = readCesium.jsonMessages(jsonMsg, nbrMsg, outbox)
            print(jsonFormat)
        else:
            readCesium.readMessages(jsonMsg, nbrMsg, outbox)

    def send(self, title, msg, recipient, outbox):
        sendCesium = SendToCesium(self.dunikey, self.pod)
        sendCesium.recipient = recipient

        # Generate pseudo-random nonce
        nonce=[]
        for _ in range(32):
            nonce.append(random.choice(string.ascii_letters + string.digits))
        sendCesium.nonce = base64.b64decode(''.join(nonce))

        finalDoc = sendCesium.configDoc(sendCesium.encryptMsg(title), sendCesium.encryptMsg(msg))       # Configure JSON document to send
        sendCesium.sendDocument(finalDoc, outbox)                                                       # Send final signed document

    def delete(self, idsMsgList, outbox):
        deleteCesium = DeleteFromCesium(self.dunikey,  self.pod)
        # deleteCesium.issuer = recipient
        for idMsg in idsMsgList:
            finalDoc = deleteCesium.configDoc(idMsg, outbox)
            deleteCesium.sendDocument(finalDoc, idMsg)


class ReadFromCesium(CesiumPlus):
    # Configure JSON document to send
    def configDoc(self, nbrMsg, outbox):
        boxType = "issuer" if outbox else "recipient"

        data = {}
        data['sort'] = { "time": "desc" }
        data['from'] = 0
        data['size'] = nbrMsg
        data['_source'] = ['issuer','recipient','title','content','time','nonce','read_signature']
        data['query'] = {}
        data['query']['bool'] = {}
        data['query']['bool']['filter'] = {}
        data['query']['bool']['filter']['term'] = {}
        data['query']['bool']['filter']['term'][boxType] = self.pubkey

        document = json.dumps(data)
        return document

    def sendDocument(self, nbrMsg, outbox):
        boxType = "outbox" if outbox else "inbox"

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
                print('\033[1m' + self.title + '\033[0m')
                print(self.content)
                
            print(colored(infoTotal.center(rows, '#'), "yellow"))
    
    # Parse JSON result and display messages
    def jsonMessages(self, msgJSON, nbrMsg, outbox):
        def decrypt(msg):
            msg64 = base64.b64decode(msg)
            return box_decrypt(msg64, get_privkey(self.dunikey, "pubsec"), self.issuer, nonce).decode()

        totalMsg = msgJSON["total"]
        if nbrMsg > totalMsg:
            nbrMsg = totalMsg

        if totalMsg == 0:
            print("Aucun message à afficher")
            return True
        else:
            data = []
            # data.append({})
            # data[0]['total'] = totalMsg
            for i, hits in enumerate(msgJSON["hits"]):
                self.idMsg = hits["_id"]
                msgSrc = hits["_source"]
                self.issuer = msgSrc["issuer"]
                nonce = msgSrc["nonce"]
                nonce = base58.b58decode(nonce)
                self.date = msgSrc["time"]

                if outbox:
                    pubkey = msgSrc["recipient"]
                else:
                    pubkey = self.issuer

                try:
                    self.title = decrypt(msgSrc["title"])
                    self.content = decrypt(msgSrc["content"])
                except Exception as e:
                    sys.stderr.write(colored(str(e), 'red') + '\n')
                    pp_json(hits)
                    continue

                data.append(i)
                data[i] = {}
                data[i]['id'] = self.idMsg
                data[i]['date'] = self.date
                data[i]['pubkey'] = pubkey
                data[i]['title'] = self.title
                data[i]['content'] = self.content

            data = json.dumps(data, indent=2)
            return data





#################### Sending class ####################




class SendToCesium(CesiumPlus):
    def encryptMsg(self, msg):
        return fmt["64"](box_encrypt(msg.encode(), get_privkey(self.dunikey, "pubsec"), self.recipient, self.nonce)).decode()

    def configDoc(self, title, msg):
        b58nonce = base58.b58encode(self.nonce).decode()

        # Get current timestamp
        timeSent = int(time.time())

        # Generate custom JSON
        data = {}
        data['issuer'] = self.pubkey
        data['recipient'] = self.recipient
        data['title'] = title
        data['content'] = msg
        data['time'] = timeSent
        data['nonce'] = b58nonce
        data['version'] = 2
        document = json.dumps(data)

        return self.signDoc(document)


    def sendDocument(self, document, outbox):
        boxType = "outbox" if outbox else "inbox"

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





#################### Deleting class ####################




class DeleteFromCesium(CesiumPlus):
    def configDoc(self, idMsg, outbox):
        # Get current timestamp
        timeSent = int(time.time())

        boxType = "outbox" if outbox else "inbox"

        # Generate document to customize
        data = {}
        data['version'] = 2
        data['index'] = "message"
        data['type'] = boxType
        data['id'] = idMsg
        data['issuer'] = self.pubkey
        data['time'] = timeSent
        document = json.dumps(data)

        return self.signDoc(document)

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





#################### Profile class ####################





class Profiles:
    def __init__(self, dunikey, pod):
        # Get my pubkey from my private key
        try:
            self.dunikey = dunikey
            if not dunikey:
                raise ValueError("Dunikey is empty")
        except:
            sys.stderr.write("Please fill the path to your private key (PubSec)\n")
            sys.exit(1)

        self.pubkey = get_privkey(dunikey, "pubsec").pubkey
        self.pod = pod

        if not re.match(PUBKEY_REGEX, self.pubkey) or len(self.pubkey) > 45:
            sys.stderr.write("La clé publique n'est pas au bon format.\n")
            sys.exit(1)

    # Configure JSON document SET to send
    def configDocSet(self, name, description, city, address, pos, socials, avatar):
        timeSent = int(time.time())

        data = {}
        if name: data['title'] = name
        if description: data['description'] = description
        if address: data['address'] = address
        if city: data['city'] = city
        if pos: 
            geoPoint = {}
            geoPoint['lat'] = pos[0]
            geoPoint['lon'] = pos[1]
            data['geoPoint'] = geoPoint
        if socials:
            data['socials'] = []
            data['socials'].append({})
            data['socials'][0]['type'] = "web"
            data['socials'][0]['url'] = socials
        if avatar:
            avatar = open(avatar, 'rb').read()
            avatar = base64.b64encode(avatar).decode()
            data['avatar'] = {}
            data['avatar']['_content'] = avatar
            data['avatar']['_content_type'] = "image/png"
        data['time'] = timeSent
        data['issuer'] = self.pubkey
        data['version'] = 2
        data['tags'] = []

        document =  json.dumps(data)

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

   # Configure JSON document GET to send
    def configDocGet(self, profile, scope='title', getAvatar=None):

        if getAvatar:
            avatar = "avatar"
        else:
            avatar = "avatar._content_type"

        data = {
                "query": {
                "bool": {
                    "should":[
                        {
                            "match":{
                                scope:{
                                    "query": profile,"boost":2
                                }
                            }
                        },{
                            "prefix": {scope: profile}
                        }
                    ]
                }
            },"highlight": {
                    "fields": {
                        "title":{},
                        "tags":{}
                    }
                },"from":0,
                "size":100,
                "_source":["title", avatar,"description","city","address","socials.url","creationTime","membersCount","type"],
                "indices_boost":{"user":100,"page":1,"group":0.01
                }
        }

        document =  json.dumps(data)

        return document

    # Configure JSON document SET to send
    def configDocErase(self):
        timeSent = int(time.time())

        data = {}
        data['time'] = timeSent
        data['id'] = self.pubkey
        data['issuer'] = self.pubkey
        data['version'] = 2
        data['index'] = "user"
        data['type'] = "profile"

        document =  json.dumps(data)

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

    def sendDocument(self, document, type):

        headers = {
            'Content-type': 'application/json',
        }

        # Send JSON document and get JSON result
        if type == 'set':
            reqQuery = '{0}/user/profile?pubkey={1}/_update?pubkey={1}'.format(self.pod, self.pubkey)
        elif type == 'get':
            reqQuery = '{0}/user,page,group/profile,record/_search'.format(self.pod)
        elif type == 'erase':
            reqQuery = '{0}/history/delete'.format(self.pod)

        result = requests.post(reqQuery, headers=headers, data=document)
        if result.status_code == 200:
            # print(result.text)
            return result.text
        else:
            sys.stderr.write("Echec de l'envoi du document...\n" + result.text + '\n')

    def parseJSON(self, doc):
        doc = json.loads(doc)['hits']['hits']
        if doc:
            pubkey = { "pubkey": doc[0]['_id'] }
            rest = doc[0]['_source']
            final = {**pubkey, **rest}
        else:
            final = 'Profile vide'

        return json.dumps(final, indent=2)


    def set(self, name=None, description=None, ville=None, adresse=None, position=None, site=None, avatar=None):
        document = self.configDocSet(name, description, ville, adresse, position, site, avatar)
        result = self.sendDocument(document,'set')

        print(result)
        return result
    
    def get(self, profile=None, avatar=None):
        if not profile:
            profile = self.pubkey
        if not re.match(PUBKEY_REGEX, profile) or len(profile) > 45:
            scope = 'title'
        else:
            scope = '_id'
        
        document = self.configDocGet(profile, scope, avatar)
        resultJSON = self.sendDocument(document, 'get')
        result = self.parseJSON(resultJSON)

        print(result)
        return result

    def erase(self):
        document = self.configDocErase()
        result = self.sendDocument(document,'erase')

        print(result)
        return result