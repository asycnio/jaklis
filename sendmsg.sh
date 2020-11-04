#!/bin/bash

# ###
# Simple testeur d'envoi de message via la messagerie de Cesium ou de Gchange.
# ###

source .env

# Help display
helpOpt() {
    echo -e "This is a simple tester for Cesium+ messages sender)
    \rOptions:
    \r$0
    Default view show last day data in cumulative mode"
}

# Parse options
declare -a args=($@)
for ((i=0; i<${#args[*]}; ++i))
do
    case ${args[$i]} in
        -f|--file) file="${args[$i+1]}";;
        -h|--help) helpOpt && exit 0;;
    esac
done

[[ -z $file ]] && file="test.txt"

# Récupération et chiffrement du titre et du message
title=$(cat $file | head -n1 | ./natools.py encrypt --pubsec -p $recipient -O 58)
content=$(cat $file | tail -n+2 | ./natools.py encrypt --pubsec -p $recipient -O 58)

times=$(date -u +'%s')
nonce=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)

# Fabrication du hash
hash="{"issuer" : "$issuer","recipient" : "$recipient","title" : "$title","content" : "$content","time" : "$times","nonce" : "$nonce"}"
hash="$(printf "%q" "$hash")"
hash=$(node -p "JSON.stringify(\"$hash\")" | sha256sum | awk '{ print $1 }')

# Fabrication de la signature
signature=$(echo "$hash" | ./natools.py sign -f pubsec -k $dunikey --noinc -O 64)

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
