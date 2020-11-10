#!/bin/bash

# ###
# Simple testeur d'envoi de message via la messagerie de Cesium ou de Gchange.
# ###

[[ -z $(which jq) || -z $(which curl) ]] && echo "Installation de jq et curl ..." && sudo apt update && sudo apt install jq curl -y

[[ ! -f .env ]] && cp .env.template .env
source .env

# Help display
helpOpt() {
    echo -e "Cesium+ messages sender
    Default: ask title, content and recipient in interactive mode.
    Advice: Fill your .env file for more fun.
    Example: $0 -f <Path of file content message> -r <recipient pubkey> -i <issuer pubkey> -k <path of pubsec keychain of issuer>

    \rOptions:
    -t\t\t\t\tTest mode: Uses the \"test.txt\" file as well as the same recipient as the sender.
    -f,--file <file>\t\tRead the file <file> with title in first line and content in rest of the file for the message.
    -r,--recipient <pubkey>\tUses <pubkey> as recipient of the message.
    -i,--issuer <pubkey>\tUses <pubkey> as issuer of the message (Could be remove in future version by calculating pubkey from privatekey).
    -k,--key <key>\t\tPath <key> to the pubsec keychain file of the issuer.
    -h,--help\t\t\tDisplay this help"
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
        *) [[ "${args[$i]}" == "-"* ]] && echo "Option inconnue." && exit 1;;
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
nonce=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
b58nonce=$(echo $nonce | base64 -d | base58)
title=$(head -n1 <<<$message | ./natools.py box-encrypt -n $nonce -f pubsec -k $dunikey -p $recipient -O 64)
content=$(tail -n+2 <<<$message | ./natools.py box-encrypt -n $nonce -f pubsec -k $dunikey -p $recipient -O 64)

times=$(date -u +'%s')

# Fabrication du hash
hashBrut="{\"issuer\":\"$issuer\",\"recipient\":\"$recipient\",\"title\":\"$title\",\"content\":\"$content\",\"time\":$times,\"nonce\":\"$b58nonce\",\"version\":2}"
hash=$(echo -n "$hashBrut" | sha256sum | cut -d ' ' -f1 | awk '{ print toupper($0) }')

# Fabrication de la signature
signature=$(echo -n "$hash" | ./natools.py sign -f pubsec -k $dunikey --noinc -O 64)

# Affichage du JSON final
document="{\"hash\":\"$hash\",\"signature\":\"$signature\",${hashBrut:1}"
jq . <<<$document

# Envoi du document
#curl -s -i -X OPTIONS "$pod/message/inbox?pubkey=$issuer" -d "pubkey=$issuer"
msgID=$(curl -s -X POST "$pod/message/inbox?pubkey=$recipient" -d "$document")
echo -e "\nMessage ID: $msgID"


### Tests mode ###

# Delete the message 1 second later, just for test
#sleep 1 && ./deletemsg.sh -id $msgID

# To put the message in outbox too
#curl -s -X POST "$pod/message/outbox?pubkey=$issuer" -d "$document"

# To put the message as read, ad this at the end of document
#,\"read_signature\":\"$signature\"
