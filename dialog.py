#!/usr/bin/env python3

import argparse, os, sys
from shutil import copyfile
if not os.path.isfile("userEnv.py"):
  copyfile("userEnv.py.template", "userEnv.py")
try:
    from userEnv import dunikey, pod
    if dunikey == "":
        raise ValueError("Dunikey is empty")
except:
    sys.stderr.write("Please fill the path to your private key (PubSec), and a Cesium ES address in userEnv.py\n")
    sys.exit(1)
from lib.cesiumMessaging import ReadFromCesium, SendToCesium, DeleteFromCesium

# Parse arguments
parser = argparse.ArgumentParser()

subparsers = parser.add_subparsers()
read_cmd = subparsers.add_parser('read', help="Lecture des messages")
send_cmd = subparsers.add_parser('send', help="Envoi d'un message")
delete_cmd = subparsers.add_parser('delete', help="Supression d'un message")

if len(sys.argv) <= 1 or not sys.argv[1] in ('read','send','delete'):
  sys.stderr.write("Veuillez indiquer une commande valide:\n\n")
  parser.print_help()
  sys.exit(1)

read_cmd.add_argument('-n', '--number',type=int, default=3, help="Affiche les NUMBER derniers messages")
read_cmd.add_argument('-o', '--outbox', action='store_true', help="Lit les messages envoyés")

send_cmd.add_argument('-d', '--destinataire', required=True, help="Destinataire du message")
send_cmd.add_argument('-t', '--titre', help="Titre du message à envoyer")
send_cmd.add_argument('-m', '--message', help="Message à envoyer")
send_cmd.add_argument('-f', '--fichier', help="Envoyer le message contenu dans le fichier 'FICHIER'")
send_cmd.add_argument('-o', '--outbox', action='store_true', help="Envoi le message sur la boite d'envoi")

delete_cmd.add_argument('-i', '--id', required=True, help="ID du message à supprimer")
delete_cmd.add_argument('-o', '--outbox', action='store_true', help="Suppression d'un message envoyé")


args = parser.parse_args()

# Build cesiumMessaging class
if sys.argv[1] == "read":
  messages = ReadFromCesium(dunikey, pod)
  messages.read(args.number, args.outbox)
elif sys.argv[1] == "send":
  if args.fichier:
    with open(args.fichier, 'r') as f:
      titre = f.readline()
      msg = ''.join(f.read().splitlines(True)[0:])
  elif args.titre and args.message:
    titre = args.titre
    msg = args.message
  else:
    titre = input("Indiquez le titre du message: ")
    msg = input("Indiquez le contenu du message: ")
  messages = SendToCesium(dunikey, pod, args.destinataire, args.outbox)
  messages.send(titre, msg)

elif sys.argv[1] == "delete":
  messages = DeleteFromCesium(dunikey, pod, args.outbox)
  messages.delete(args.id)

