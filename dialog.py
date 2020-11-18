#!/usr/bin/env python3

import argparse, os, sys
from shutil import copyfile
if not os.path.isfile("userEnv.py"):
  copyfile("userEnv.py.template", "userEnv.py")
try:
    from userEnv import dunikey, pod
except:
    sys.stderr.write("Please fill the path to your private key (PubSec), and a Cesium ES address in userEnv.py\n")
    sys.exit(1)
from lib.cesiumMessaging import ReadFromCesium

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('-n', '--number',type=int, default=3, help="Affiche les NUMBER derniers messages")
parser.add_argument('-o', '--outbox', action='store_true', help="Lecture des messages envoyés")
args = parser.parse_args()

# Build ReadFromCesium object
messages = ReadFromCesium(dunikey, pod)
messages.read(args.number, args.outbox)
# print(messages.sendDocument(args.number, args.outbox)) # For debug, print complete JSON answer

