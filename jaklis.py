#!/usr/bin/env python3

import argparse, sys, os, getpass, string, random
from os.path import join, dirname
from shutil import copyfile
from dotenv import load_dotenv
from duniterpy.key import SigningKey

__version__ = "0.0.2"

MY_PATH = os.path.realpath(os.path.dirname(sys.argv[0])) + '/'

# Get variables environment
if not os.path.isfile(MY_PATH + '.env'):
    copyfile(MY_PATH + ".env.template",MY_PATH +  ".env")
dotenv_path = join(dirname(__file__),MY_PATH +  '.env')
load_dotenv(dotenv_path)

# Parse arguments
parser = argparse.ArgumentParser(description="Client CLI pour Cesium+ et Ḡchange")
parser.add_argument('-v', '--version', action='store_true', help="Affiche la version actuelle du programme")
parser.add_argument('-k', '--key', help="Chemin vers mon trousseau de clé (PubSec)")
parser.add_argument('-n', '--node', help="Adresse du noeud Cesium+, Gchange ou Duniter à utiliser")

subparsers = parser.add_subparsers(title="Commandes de jaklis", dest="cmd")
read_cmd = subparsers.add_parser('read', help="Lecture des messages")
send_cmd = subparsers.add_parser('send', help="Envoi d'un message")
delete_cmd = subparsers.add_parser('delete', help="Supression d'un message")
getProfile_cmd = subparsers.add_parser('get', help="Voir un profile Cesium+")
setProfile_cmd = subparsers.add_parser('set', help="Configurer son profile Cesium+")
eraseProfile_cmd = subparsers.add_parser('erase', help="Effacer son profile Cesium+")
like_cmd = subparsers.add_parser('like', help="Voir les likes d'un profile / Liker un profile (option -s NOTE)")
unlike_cmd = subparsers.add_parser('unlike', help="Supprimer un like")
pay_cmd = subparsers.add_parser('pay', help="Payer en Ḡ1")
history_cmd = subparsers.add_parser('history', help="Voir l'historique des transactions d'un compte Ḡ1")
balance_cmd = subparsers.add_parser('balance', help="Voir le solde d'un compte Ḡ1")

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

# GVA usage
pay_cmd.add_argument('-p', '--pubkey', help="Destinataire du paiement")
pay_cmd.add_argument('-a', '--amount', type=float, help="Montant de la transaction")
pay_cmd.add_argument('-c', '--comment',  default="", help="Commentaire de la transaction")
pay_cmd.add_argument('-m', '--mempool', action='store_true', help="Utilise les sources en Mempool")
pay_cmd.add_argument('-v', '--verbose', action='store_true', help="Affiche le résultat JSON de la transaction")

history_cmd.add_argument('-p', '--pubkey', help="Clé publique du compte visé")
history_cmd.add_argument('-j', '--json',  action='store_true', help="Affiche le résultat en format JSON")
history_cmd.add_argument('--nocolors',  action='store_true', help="Affiche le résultat en noir et blanc")

balance_cmd.add_argument('-p', '--pubkey', help="Clé publique du compte visé")
balance_cmd.add_argument('-m', '--mempool', action='store_true', help="Utilise les sources en Mempool")


args = parser.parse_args()
cmd = args.cmd

if args.version:
  print(__version__)
  sys.exit(0)

if not cmd:
    parser.print_help()
    sys.exit(1)

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

# Check if we need dunikey
try:
    pubkey = args.pubkey
except:
    pubkey = False
try:
    profile = args.profile
except:
    profile = False

if cmd in ('history','balance','get') and (pubkey or profile):
    noNeedDunikey = True
    keyPath = False
    try:
        dunikey = args.pubkey
    except:
        dunikey = args.profile
else:
    noNeedDunikey = False
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


# Construct CesiumPlus object
if cmd in ("read","send","delete","set","get","erase","like","unlike"):
    from lib.cesium import CesiumPlus

    if args.node:
        pod = args.node
    else:
        pod = os.getenv('POD')
    if not pod:
        pod="https://g1.data.le-sou.org"

    cesium = CesiumPlus(dunikey, pod, noNeedDunikey)

    # Messaging
    if cmd == "read":
        cesium.read(args.number, args.outbox, args.json)
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

        cesium.send(titre, msg, args.destinataire, args.outbox)

    elif cmd == "delete":
        cesium.delete(args.id[0], args.outbox)

    # Profiles
    elif cmd == "set":
        cesium.set(args.name, args.description, args.ville, args.adresse, args.position, args.site, args.avatar)
    elif cmd == "get":
        cesium.get(args.profile, args.avatar)
    elif cmd == "erase":
        cesium.erase()

    # Likes
    elif cmd == "like":
        if args.stars or args.stars == 0:
            cesium.like(args.stars, args.profile)
        else:
            cesium.readLikes(args.profile)
    elif cmd == "unlike":
        cesium.unLike(args.profile)

# Construct GVA object
elif cmd in ("pay","history","balance"):
    from lib.gva import GvaApi

    if args.node:
        node = args.node
    else:
        node = os.getenv('NODE')
    if not node:
        node="https://g1.librelois.fr/gva"

    if args.pubkey:
        destPubkey = args.pubkey
    else:
        destPubkey = False

    gva = GvaApi(dunikey, node, destPubkey, noNeedDunikey)

    if cmd == "pay":
        gva.pay(args.amount, args.comment, args.mempool, args.verbose)
    if cmd == "history":
        gva.history(args.json, args.nocolors)
    if cmd == "balance":
        gva.balance(args.mempool)


if keyPath:
    os.remove(keyPath)
