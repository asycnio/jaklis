#!/usr/bin/env python3

import argparse, sys, os
from os.path import join, dirname
from shutil import copyfile
from dotenv import load_dotenv
from lib.cesium import Profiles

VERSION = "0.1.1"

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
if not os.path.isfile(dunikey):
    HOME = os.getenv("HOME")
    dunikey = HOME + os.getenv('DUNIKEY')
if not os.path.isfile(dunikey):
    sys.stderr.write("File {0} doesn't exist.\n".format(dunikey))
    sys.exit(1)

# Parse arguments
parser = argparse.ArgumentParser()

subparsers = parser.add_subparsers()
getProfile_cmd = subparsers.add_parser('get', help="Voir un profile Cesium+")
setProfile_cmd = subparsers.add_parser('set', help="Configurer son profile Cesium+")
eraseProfile_cmd = subparsers.add_parser('erase', help="Effacer son profile Cesium+")

if len(sys.argv) <= 1 or not sys.argv[1] in ('set','get','erase'):
    sys.stderr.write("Veuillez indiquer une commande valide:\n\n")
    parser.print_help()
    sys.exit(1)

setProfile_cmd.add_argument('-n', '--name', help="Nom du profile")
setProfile_cmd.add_argument('-d', '--description', help="Description du profile")
setProfile_cmd.add_argument('-v', '--ville', help="Ville du profile")
setProfile_cmd.add_argument('-a', '--adresse', help="Adresse du profile")
setProfile_cmd.add_argument('-pos', '--position', nargs=2, help="Points géographiques (lat + lon)")
setProfile_cmd.add_argument('-s', '--site', help="Site web du profile")

getProfile_cmd.add_argument('-p', '--profile', help="Nom du profile")

args = parser.parse_args()

# Build gchange class
cesium = Profiles(dunikey, pod)
if sys.argv[1] == "set":
    cesium.set(args.name, args.description, args.ville, args.adresse, args.position, args.site)
elif sys.argv[1] == "get":
    cesium.get(args.profile)
elif sys.argv[1] == "erase":
    cesium.erase()
