#!/bin/bash

# ###
# Simple testeur d'envoi de message via la messagerie de Cesium ou de Gchange.
# ###

[[ ! -f .env ]] && cp .env.template .env
source .env

# Help display
helpOpt() {
    echo -e "This is a simple tester for Cesium+ messages sending
    \r$0
    Default, ask title, content and recipient in interactive mode.

    \rOptions:
    -t\t\t\t\tTest mode: Uses the \"test.txt\" file as well as the same recipient as the sender.
    -f,--file <file>\t\tRead the file <file> with title in first line and content in rest of the file for the message.
    -r,--recipient <pubkey>\tUses <pubkey> as recipient of the message.
    -i,--issuer <pubkey>\tUses <pubkey> as issuer of the message.
    -k,--key <key>\t\tPath <key> to the pubsec keychain file of the issuer."
}

REGEX_PUBKEYS="[a-zA-Z0-9]{42,44}"

# Parse options
declare -a args=($@)
for ((i=0; i<${#args[*]}; ++i))
do
    case ${args[$i]} in
        -f|--file) file="${args[$i+1]}"
            [[ ! -f $file ]] && echo "Le fichier $file n'existe pas." && exit 1;;
        -t|--test) file="test.txt"
            recipient=$issuer;;
        -r|--recipient) recipient="${args[$i+1]}"
            [[ -z $recipient ]] && echo "Veuillez préciser un destinataire." && exit 1;;
        -i|--issuer) issuer="${args[$i+1]}"
            [[ -z $issuer ]] && echo "Veuillez préciser un émetteur." && exit 1;;
        -k|--key) dunikey="${args[$i+1]}"
            [[ -z $dunikey ]] && echo "Veuillez préciser un fichier de trousseau." && exit 1;;
        -h|--help) helpOpt && exit 0;;
    esac
done

if [[ -z $file ]]; then
    read -p "Objet du message: " title
    read -p "Corps du message: " content
    message="$title"$'\n'"$content"
else
    message=$(cat $file)
fi
if [[ -z $issuer ]]; then
    read -p "Émetteur: " issuer
fi
if [[ -z $recipient ]]; then
    read -p "Destinataire: " recipient
fi
if [[ -z $dunikey ]]; then
    read -p "Fichier de trousseau: " dunikey
fi

[[ -z $(grep -Eo $REGEX_PUBKEYS <<<$recipient) ]] && echo "Le format de la clé publique du destinataire est invalide." && exit 1
[[ -z $(grep -Eo $REGEX_PUBKEYS <<<$issuer) ]] && echo "Le format de la clé publique de l'émetteur est invalide." && exit 1

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

# Envoi du document
curl -X POST "$pod/message/inbox" -d "{\"issuer\":\"$issuer\",\"recipient\":\"$recipient\",\"title\":\"$title\",\"content\":\"$content\",\"time\":$times,\"nonce\":\"$nonce\",\"version\":2,\"hash\":\"$hash\",\"signature\":\"$signature\"}"
