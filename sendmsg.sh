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

REGEX_PUBKEYS="[a-zA-Z0-9]{42,44}"

# Parse options
declare -a args=($@)
for ((i=0; i<${#args[*]}; ++i))
do
    case ${args[$i]} in
        -f|--file) file="${args[$i+1]}"
            [[ ! -f $file ]] && echo "Le fichier $file n'existe pas." && exit 1;;
        -t|--test) file="test.txt";;
        -r|--recipient) recipient="${args[$i+1]}"
            [[ -z $recipient ]] && echo "Veuillez préciser un destinataire." && exit 1;;
        -k|--key) dunikey="${args[$i+1]}"
            [[ -z $dunikey ]] && echo "Veuillez préciser un fichier de trousseau." && exit 1;;
        -h|--help) helpOpt && exit 0;;
    esac
done

[[ -z $(grep -Eo $REGEX_PUBKEYS <<<$recipient) ]] && echo "Le format de la clé publique du destinataire est invalide." && exit 1

if [[ -z $file ]]; then
    read -p "Objet du message: " title
    read -p "Corps du message: " content
    message="$title"$'\n'"$content"
else
    message=$(cat $file)
fi

# Récupération et chiffrement du titre et du message
title=$(head -n1 <<<$message | ./natools.py encrypt --pubsec -p $recipient -O 58)
content=$(tail -n+2 <<<$message | ./natools.py encrypt --pubsec -p $recipient -O 58)

# title="78FPlouMe63I49IzyNY1B2Uh6s8mBBoBZA=="
# content="78FPlouMe63I49IzyNY1B2Uh6s8mBBoBZA=="

times=$(date -u +'%s')
nonce=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)

# Fabrication du hash
hash="{\"issuer\":\"$issuer\",\"recipient\":\"$recipient\",\"title\":\"$title\",\"content\":\"$content\",\"time\":$times,\"nonce\":\"$nonce\",\"version\":2}"
hash=$(echo -n "$hash" | sha256sum | cut -d ' ' -f1 | awk '{ print toupper($0) }')

# Fabrication de la signature
signature=$(echo -n "$hash" | ./natools.py sign -f pubsec -k $dunikey --noinc -O 64)

# Affichage du JSON final
echo "{
    "issuer" : \"$issuer\",
    "recipient" : \"$recipient\",
    "title" : \"$title\",
    "content" : \"$content\",
    "time" : "$times",
    "nonce" : \"$nonce\",
    "version" : 2,
    "hash" : \"$hash\",
    "signature" : \"$signature\"
}"

# Envoi du document à
curl -X POST "$pod/message/inbox" -d "{\"issuer\":\"$issuer\",\"recipient\":\"$recipient\",\"title\":\"$title\",\"content\":\"$content\",\"time\":$times,\"nonce\":\"$nonce\",\"version\":2,\"hash\":\"$hash\",\"signature\":\"$signature\"}"
