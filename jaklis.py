#!/usr/bin/env python3

import argparse, sys, os, random, string, getpass
from os.path import join, dirname
from shutil import copyfile
from dotenv import load_dotenv
from duniterpy.key import SigningKey
from lib.cesium import ReadFromCesium, SendToCesium, DeleteFromCesium, Profiles
from lib.likes import ReadLikes, SendLikes, UnLikes

VERSION = "0.0.1"

# Get variables environment
if not os.path.isfile('.env'):
    copyfile(".env.template", ".env")
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('-v', '--version', action='store_true', help="Affiche la version actuelle du programme")
parser.add_argument('-k', '--key', help="Chemin vers mon trousseau de clé (PubSec)")
parser.add_argument('-n', '--node', help="Adresse du noeud Cesium+ ou Gchange à utiliser")

subparsers = parser.add_subparsers()
read_cmd = subparsers.add_parser('read', help="Lecture des messages")
send_cmd = subparsers.add_parser('send', help="Envoi d'un message")
delete_cmd = subparsers.add_parser('delete', help="Supression d'un message")
getProfile_cmd = subparsers.add_parser('get', help="Voir un profile Cesium+")
setProfile_cmd = subparsers.add_parser('set', help="Configurer son profile Cesium+")
eraseProfile_cmd = subparsers.add_parser('erase', help="Effacer son profile Cesium+")
like_cmd = subparsers.add_parser('like', help="Voir les likes d'un profile / Liker un profile (option -s NOTE)")
unlike_cmd = subparsers.add_parser('unlike', help="Supprimer un like")

if sys.argv[1] in ('-k','-n'):
    if sys.argv[3] in ('-k','-n'):
        cmd = sys.argv[5]
    else:
        cmd = sys.argv[3]
else:
    cmd = sys.argv[1]

if len(sys.argv) <= 1 or not cmd in ('read','send','delete','set','get','erase','like','unlike','-v','--version'):
    sys.stderr.write("Veuillez indiquer une commande valide:\n\n")
    parser.print_help()
    sys.exit(1)

# Messages management
read_cmd.add_argument('-n', '--number',type=int, default=3, help="Affiche les NUMBER derniers messages")
read_cmd.add_argument('-j', '--json', action='store_true', help="Sort au format JSON")
read_cmd.add_argument('-o', '--outbox', action='store_true', help="Lit les messages envoyés")

send_cmd.add_argument('-d', '--destinataire', required=True, help="Destinataire du message")
send_cmd.add_argument('-t', '--titre', help="Titre du message à envoyer")
send_cmd.add_argument('-m', '--message', help="Message à envoyer")
send_cmd.add_argument('-f', '--fichier', help="Envoyer le message contenu dans le fichier 'FICHIER'")
send_cmd.add_argument('-o', '--outbox', action='store_true', help="Envoi le message sur la boite d'envoi")

delete_cmd.add_argument('-i', '--id', action='append', nargs='+', required=True, help="ID(s) du/des message(s) à supprimer")
delete_cmd.add_argument('-o', '--outbox', action='store_true', help="Suppression d'un message envoyé")

# Profiles management
setProfile_cmd.add_argument('-n', '--name', help="Nom du profile")
setProfile_cmd.add_argument('-d', '--description', help="Description du profile")
setProfile_cmd.add_argument('-v', '--ville', help="Ville du profile")
setProfile_cmd.add_argument('-a', '--adresse', help="Adresse du profile")
setProfile_cmd.add_argument('-pos', '--position', nargs=2, help="Points géographiques (lat + lon)")
setProfile_cmd.add_argument('-s', '--site', help="Site web du profile")
setProfile_cmd.add_argument('-A', '--avatar', help="Chemin vers mon avatar en PNG")

getProfile_cmd.add_argument('-p', '--profile', help="Nom du profile")
getProfile_cmd.add_argument('-a', '--avatar', action='store_true', help="Récupérer également l'avatar au format raw base64")

# Likes management
like_cmd.add_argument('-p', '--profile', help="Profile cible")
like_cmd.add_argument('-s', '--stars', type=int, help="Nombre d'étoile")
unlike_cmd.add_argument('-p', '--profile', help="Profile à déliker")

args = parser.parse_args()

if args.version:
  print(VERSION)
  sys.exit(0)

def createTmpDunikey():
    # Generate pseudo-random nonce
    nonce=[]
    for _ in range(32):
        nonce.append(random.choice(string.ascii_letters + string.digits))
    nonce = ''.join(nonce)
    keyPath = "/tmp/secret.dunikey-" + nonce

    key = SigningKey.from_credentials(getpass.getpass("Identifiant: "), getpass.getpass("Mot de passe: "), None)
    key.save_pubsec_file(keyPath)
    
    return keyPath

if args.node:
    pod = args.node
else:
    pod = os.getenv('POD')
if not pod:
    pod="https://g1.data.le-sou.org"

if args.key:
    dunikey = args.key
    keyPath = False
else:
    dunikey = os.getenv('DUNIKEY')
    if not dunikey:
        keyPath = createTmpDunikey()
        dunikey = keyPath
    else:
        keyPath = False
if not os.path.isfile(dunikey):
    HOME = os.getenv("HOME")
    dunikey = HOME + dunikey
    if not os.path.isfile(dunikey):
        sys.stderr.write('Le fichier de trousseau {0} est introuvable.\n'.format(dunikey))
        sys.exit(1)


# Build cesiumMessaging class
if cmd == "read":
    messages = ReadFromCesium(dunikey, pod)
    messages.read(args.number, args.outbox, args.json)
elif cmd == "send":
    if args.fichier:
        with open(args.fichier, 'r') as f:
            msgT = f.read()
            titre = msgT.splitlines(True)[0].replace('\n', '')
            msg = ''.join(msgT.splitlines(True)[1:])
            if args.titre:
                titre = args.titre
                msg = msgT
    elif args.titre and args.message:
        titre = args.titre
        msg = args.message
    else:
        titre = input("Indiquez le titre du message: ")
        msg = input("Indiquez le contenu du message: ")

    messages = SendToCesium(dunikey, pod, args.destinataire, args.outbox)
    messages.send(titre, msg)

elif cmd == "delete":
    messages = DeleteFromCesium(dunikey, pod, args.outbox)
    messages.delete(args.id[0])

# Build cesium+ profiles class
elif cmd in ('set','get','erase'):
    cesium = Profiles(dunikey, pod)
    if cmd == "set":
        cesium.set(args.name, args.description, args.ville, args.adresse, args.position, args.site, args.avatar)
    elif cmd == "get":
        cesium.get(args.profile, args.avatar)
    elif cmd == "erase":
        cesium.erase()

# Build cesium+ likes class
elif cmd == "like":
    if args.stars or args.stars == 0:
        gchange = SendLikes(dunikey, pod)
        gchange.like(args.stars, args.profile)
    else:
        gchange = ReadLikes(dunikey, pod)
        gchange.readLikes(args.profile)
elif cmd == "unlike":
    gchange = UnLikes(dunikey, pod)
    gchange.unLike(args.profile)


if keyPath:
    os.remove(keyPath)
