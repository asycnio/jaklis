#!/usr/bin/env python3

import os, sys, ast, requests, json, base58, base64, time, string, random, re
from lib.natools import fmt, sign, get_privkey, box_decrypt, box_encrypt
from time import sleep
from hashlib import sha256
from datetime import datetime
from termcolor import colored

PUBKEY_REGEX = "(?![OIl])[1-9A-Za-z]{42,45}"

class ReadLikes:
    def __init__(self, dunikey, pod):
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

        if not re.match(PUBKEY_REGEX, self.issuer) or len(self.issuer) > 45:
            sys.stderr.write("La clé publique n'est pas au bon format.\n")
            sys.exit(1)

    # Configure JSON document to send
    def configDoc(self, profile):
        if not profile: profile = self.issuer
        # elif len(profile) < 42:
        #     print(len(profile))
        #     gProfile = requests.get('{0}/user/profile/{1}'.format(self.pod, issuer))
        #     gProfile = json.loads(gProfile.text)['_source']
        #     pseudo = gProfile['title']

        data = {}
        data['query'] = {}
        data['query']['bool'] = {}
        data['query']['bool']['filter'] = [
            {'term': {'index': 'user'}},
            {'term': {'type': 'profile'}},
            {'term': {'id': profile}},
            {'term': {'kind': 'STAR'}}
        ]
        # data['query']['bool']['should'] = {'term':{'issuer': self.issuer}}
        data['size'] = 5000
        data['_source'] = ['issuer','level']
        data['aggs'] = {
            'level_sum': {
                'sum': {
                    'field': 'level'
                }
            }
        }

        return json.dumps(data)

    def sendDocument(self, document):

        headers = {
            'Content-type': 'application/json',
        }

        # Send JSON document and get JSON result
        result = requests.post('{0}/like/record/_search'.format(self.pod), headers=headers, data=document)

        if result.status_code == 200:
            # print(result.text)
            return result.text
        else:
            sys.stderr.write("Echec de l'envoi du document de lecture des messages...\n" + result.text + '\n')

    def parseResult(self, result):
        result = json.loads(result)
        totalLikes = result['hits']['total']
        totalValue = result['aggregations']['level_sum']['value']
        if totalLikes:
            score = totalValue/totalLikes
        else:
            score = 0
        raw = result['hits']['hits']
        finalPrint = {}
        finalPrint['likes'] = []
        for i in raw:
            issuer = i['_source']['issuer']
            gProfile = self.getProfile(issuer)
            pseudo = gProfile['title']
            payTo = gProfile['pubkey']
            id = i['_id']
            level = i['_source']['level']
            if issuer == self.issuer:
                finalPrint['yours'] = { 'id' : id, 'level' : level }
            else:
                finalPrint['likes'].append({ 'issuer' : issuer, 'pseudo' : pseudo, 'payTo' : payTo, 'level' : level })
        finalPrint['score'] = score

        return json.dumps(finalPrint)

    def getProfile(self, profile):
        headers = {
            'Content-type': 'application/json',
        }

        data = {}
        data['query'] = {}
        data['query']['bool'] = {}
        data['query']['bool']['filter'] = [
            {'term': {'_index': 'user'}},
            {'term': {'_type': 'profile'}},
            {'term': {'_id': profile}}
        ]
        data['_source'] = ['title','pubkey']

        data = json.dumps(data)

        result = requests.post('{0}/user/profile/_search'.format(self.pod), headers=headers, data=data)
        result = json.loads(result.text)['hits']['hits'][0]['_source']
        
        return result

    def readLikes(self, profile=False):
        document = self.configDoc(profile)
        result = self.sendDocument(document)
        result = self.parseResult(result)

        print(result)
        return result




#################### Like class ####################




class SendLikes:
    def __init__(self, dunikey, pod):
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

        if not re.match(PUBKEY_REGEX, self.issuer) or len(self.issuer) > 45:
            sys.stderr.write("La clé publique n'est pas au bon format.\n")
            sys.exit(1)

    # Configure JSON document to send
    def configDoc(self, profile, likes):
        if not profile: profile = self.issuer
        if likes not in range(0, 6):
            sys.stderr.write(colored('Votre like doit être compris entre 0 et 5.\n', 'red'))
            return False


        timeSent = int(time.time())

        data = {}
        data['version'] = 2
        data['index'] = "user"
        data['type'] = "profile"
        data['id'] = profile
        data['kind'] = "STAR"
        data['level'] = likes
        data['time'] = timeSent
        data['issuer'] = self.issuer

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

    def sendDocument(self, document, pubkey):

        headers = {
            'Content-type': 'application/json',
        }

        # Send JSON document and get JSON result
        result = requests.post('{0}/user/profile/:id/_like'.format(self.pod), headers=headers, data=document)

        if result.status_code == 200:
            print(colored("Profile liké avec succès !", 'green'))
            return result.text
        elif result.status_code == 400:
            resultJson = json.loads(result.text)
            if 'DuplicatedDocumentException' in resultJson['error']:
                rmLike = UnLikes(self.dunikey, self.pod)
                rmLike.unLike(pubkey, True)
                sleep(0.5)
                self.sendDocument(document, pubkey)
                return resultJson['error']
            else:
                sys.stderr.write("Echec de l'envoi du document de lecture des messages...\n" + resultJson['error'] + '\n')
        else:
            resultJson = json.loads(result.text)
            sys.stderr.write("Echec de l'envoi du document de lecture des messages...\n" + resultJson['error'] + '\n')




    def like(self, stars, profile=False):
        document = self.configDoc(profile, stars)
        if document:
            self.sendDocument(document, profile)




#################### Unlike class ####################




class UnLikes:
    def __init__(self, dunikey, pod):
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

        if not re.match(PUBKEY_REGEX, self.issuer) or len(self.issuer) > 45:
            sys.stderr.write("La clé publique n'est pas au bon format.\n")
            sys.exit(1)
    
    # Check if you liked this profile
    def checkLike(self, pubkey):

        readProfileLikes = ReadLikes(self.dunikey, self.pod)
        document = readProfileLikes.configDoc(pubkey)
        result = readProfileLikes.sendDocument(document)
        result = readProfileLikes.parseResult(result)
        result = json.loads(result)

        if 'yours' in result:
            myLike = result['yours']['id']
            return myLike
        else:
            sys.stderr.write("Vous n'avez pas liké ce profile\n")
            return False

    # Configure JSON document to send
    def configDoc(self, idLike):
        timeSent = int(time.time())

        data = {}
        data['version'] = 2
        data['index'] = "like"
        data['type'] = "record"
        data['id'] = idLike
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

    def sendDocument(self, document, silent):

        headers = {
            'Content-type': 'application/json',
        }

        # Send JSON document and get JSON result
        result = requests.post('{0}/history/delete'.format(self.pod), headers=headers, data=document)

        if result.status_code == 200:
            if not silent:
                print(colored("Like supprimé avec succès !", 'green'))
            return result.text
        else:
            sys.stderr.write("Echec de l'envoi du document de lecture des messages...\n" + result.text + '\n')


    def unLike(self, pubkey, silent=False):
        idLike = self.checkLike(pubkey)
        if idLike:
            document = self.configDoc(idLike)
            self.sendDocument(document, silent)

