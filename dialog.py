#!/usr/bin/env python3

import argparse, sys, os
from os.path import join, dirname
from shutil import copyfile
from dotenv import load_dotenv
from lib.cesiumMessaging import ReadFromCesium, SendToCesium, DeleteFromCesium, VERSION

# Get varriables environment
if not os.path.isfile('.env'):
    copyfile(".env.template", ".env")
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

dunikey = os.getenv('DUNIKEY')
pod = os.getenv('POD')
if not dunikey or not pod:
    sys.stderr.write("Please fill the path of your private key (PubSec), and a Cesium ES address in .env file\n")
    sys.exit(1)


# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('-v', '--version', action='store_true', help="Affiche la version actuelle du programme")

subparsers = parser.add_subparsers()
read_cmd = subparsers.add_parser('read', help="Lecture des messages")
send_cmd = subparsers.add_parser('send', help="Envoi d'un message")
delete_cmd = subparsers.add_parser('delete', help="Supression d'un message")

if len(sys.argv) <= 1 or not sys.argv[1] in ('read','send','delete','-v','--version'):
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

delete_cmd.add_argument('-i', '--id', action='append', nargs='+', required=True, help="ID(s) du/des message(s) à supprimer")
delete_cmd.add_argument('-o', '--outbox', action='store_true', help="Suppression d'un message envoyé")

args = parser.parse_args()

if args.version:
  print(VERSION)
  sys.exit(0)

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
    messages.delete(args.id[0])

