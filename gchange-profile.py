#!/usr/bin/env python3

import argparse, sys, os
from os.path import join, dirname
from shutil import copyfile
from dotenv import load_dotenv
from lib.gchange import ReadLikes, SendLikes, DeleteLikes

# Get variables environment
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

subparsers = parser.add_subparsers()
readLike_cmd = subparsers.add_parser('readlike', help="Lire les likes d'un profile")
like_cmd = subparsers.add_parser('like', help="Liker un profile")
deleteLike_cmd = subparsers.add_parser('deletelike', help="Supprimer un like")

if len(sys.argv) <= 1 or not sys.argv[1] in ('readlike','like','deletelike'):
    sys.stderr.write("Veuillez indiquer une commande valide:\n\n")
    parser.print_help()
    sys.exit(1)

readLike_cmd.add_argument('-p', '--profile', help="Profile cible")

like_cmd.add_argument('-p', '--profile', help="Profile cible")
like_cmd.add_argument('-s', '--stars', type=int, help="Nombre d'étoile")

deleteLike_cmd.add_argument('-i', '--id', help="ID du like à supprimer")

args = parser.parse_args()

# Build gchange class
if sys.argv[1] == "readlike":
    gchange = ReadLikes(dunikey, pod)
    gchange.readLikes(args.profile)
elif sys.argv[1] == "like":
    gchange = SendLikes(dunikey, pod)
    gchange.like(args.profile, args.stars)
elif sys.argv[1] == "deletelike":
    gchange = DeleteLikes(dunikey, pod)
    gchange.deleteLike(args.id)

