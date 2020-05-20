#!/bin/bash

# ###
# Simple testeur d'envoi de message via la messagerie de Cesium ou de Gchange.
# ###

# Variable utilisateur
issuer="Do99s6wQR2JLfhirPdpAERSjNbmjjECzGxHNJMiNKT3P"		# Clé publique Ḡ1 de l'émetteur du message
recipient="DsEx1pS33vzYZg4MroyBV9hCw98j1gtHEhwiZ5tK7ech"	# Clé publique Ḡ1 du destinataire du message
dunikey="~/dev/trousseau-Do99s6wQ-g1-PubSec.dunikey"		# La clé privé Ḡ1 de l'émetteur, générable par Cesium au format PubSec
#pod="https://data.gchange.fr"								# Adresse du pod Cesium ou Gchange à utiliser
pod="https://g1.data.duniter.fr"
###


# Récupération et chiffrement du titre et du message
title=$(./natools.py encrypt -i helloworld/title --pubsec -p DsEx1pS33vzYZg4MroyBV9hCw98j1gtHEhwiZ5tK7ech -O 58)
content=$(./natools.py encrypt -i helloworld/content --pubsec -p DsEx1pS33vzYZg4MroyBV9hCw98j1gtHEhwiZ5tK7ech -O 58)

times=$(date -u +'%s')
nonce=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)

# Fabrication du hash
hash="{"issuer" : "$issuer","recipient" : "$recipient","title" : "$title","content" : "$content","time" : "$times","nonce" : "$nonce"}"
hash="$(printf "%q" "$hash")"
hash=$(node -p "JSON.stringify(\"$hash\")" | sha256sum | awk '{ print $1 }')

# Fabrication de la signature
signature=$(echo "$hash" | ./natools.py sign --pubsec -k ~/dev/trousseau-Do99s6wQ-g1-PubSec.dunikey --noinc -O 64)

# Affichage du JSON final
echo "{
    "issuer" : \"$issuer\",
    "recipient" : \"$recipient\",
    "title" : \"$title\",
    "content" : \"$content\",
    "time" : "$times",
    "nonce" : \"$nonce\",
    "hash" : \"$hash\",
    "signature" : \"$signature\"
}"

# Envoi du document à
curl "$pod/message/outbox" -d '
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
