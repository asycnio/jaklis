#!/bin/bash

# ###
# Simple testeur d'envoi de message via la messagerie de Cesium ou de Gchange.
# ###

# Variable utilisateur
issuer="Do99s6wQR2JLfhirPdpAERSjNbmjjECzGxHNJMiNKT3P"		# Clé publique Ḡ1 de l'émetteur du message
recipient="DsEx1pS33vzYZg4MroyBV9hCw98j1gtHEhwiZ5tK7ech"	# Clé publique Ḡ1 du destinataire du message
dunikey="~/dev/trousseau-Do99s6wQ-g1-PubSec.dunikey"		# La clé privé Ḡ1 de l'émetteur, générable par Cesium au format PubSec
pod="https://data.gchange.fr"								# Adresse du pod Cesium ou Gchange à utiliser
###


# Récupération et chiffrement du titre et du message
title=$(./natools.py encrypt -i helloworld/title --pubsec -p DsEx1pS33vzYZg4MroyBV9hCw98j1gtHEhwiZ5tK7ech | base58)
content=$(./natools.py encrypt -i helloworld/content --pubsec -p DsEx1pS33vzYZg4MroyBV9hCw98j1gtHEhwiZ5tK7ech | base58)

times=$(date -u +'%s')
nonce=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)

# Fabrication du hash
hash=$(echo "{
    "issuer" : "$issuer",
    "recipient" : "$recipient",
    "title" : "$title",
    "content" : "$content",
    "time" : "$times",
    "nonce" : "$nonce",
}" | sha256sum | awk '{ print $1 }')
hash=$(node -p "JSON.stringify(\"$hash\")")

# Fabrication de la signature
signature=$(echo "$hash" | ./natools.py sign --pubsec -k ~/dev/trousseau-Do99s6wQ-g1-PubSec.dunikey --noinc | base64)

# Affichage du JSON final
echo "{
    "issuer" : \"$issuer\",
    "recipient" : \"$recipient\",
    "title" : \"$title\",
    "content" : \"$content\",
    "time" : "$times",
    "nonce" : \"$nonce\",
    "hash" : "$hash",
    "signature" : \"$signature\"
}"

# Envoi du document à
curl -s "$pod/message/outbox" -d '
{
    "issuer" : "$issuer",
    "recipient" : "$recipient",
    "title" : "$title",
    "content" : "$content",
    "time" : "$times",
    "nonce" : "$nonce",
    "hash" : "$hash",
    "signature" : "$signature"
}'
