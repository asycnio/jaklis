#!/bin/bash

# ###
# Lecture des messages Cesium+
# ###

[[ -z $(which jq) || -z $(which curl) ]] && echo "Installation de jq et curl ..." && sudo apt update && sudo apt install jq curl -y

[[ ! -f .env ]] && cp .env.template .env
source .env

# Help display
helpOpt() {
    echo -e "Cesium+ messages sender
    \r$0
    Default: ask recipient in interactive mode.
    Advice: Fill your .env file for more fun.

    \rOptions:
    -k,--key <key>\t\tPath <key> to the pubsec keychain file of the issuer.
    -n,--number <number>\tDisplay the <number> lasts messages from Cesium (tail-like format)
    -o,--outbox\t\t\tRead outbox messages instead of inbox
    -h,--help\t\t\tDisplay this help"
}

REGEX_PUBKEYS="[a-zA-Z0-9]{42,44}"

recipient=$issuer

# Parse options
declare -a args=($@)
for ((i=0; i<${#args[*]}; ++i))
do
    case ${args[$i]} in
        -k|--key) dunikey="${args[$i+1]}"
            [[ -z $dunikey ]] && echo "Veuillez préciser un fichier de trousseau." && exit 1;;
        -o|--outbox) type=outbox;;
        -n|--number) nbrRaw="${args[$i+1]}";;
        -n*) nbrRaw="${args[$i]:2}";;
        -h|--help) helpOpt && exit 0;;
        *) [[ "${args[$i]}" == "-"* ]] && echo "Option inconnue." && exit 1;;
    esac
done


recipient=$(./natools.py pk -f pubsec -k $dunikey)
if [[ -z $dunikey ]]; then
    read -p "Fichier de trousseau: " dunikey
fi
[[ -z $type ]] && type="inbox"
[[ -z $nbrRaw ]] && nbrRaw=5000

[[ -z $(grep -Eo $REGEX_PUBKEYS <<<$recipient) ]] && echo "Le format de la clé publique du destinataire est invalide." && exit 1

document="{\"sort\":{\"time\":\"desc\"},\"from\":0,\"size\":$nbrRaw,\"_source\":[\"issuer\",\"recipient\",\"title\",\"content\",\"time\",\"nonce\",\"read_signature\"],\"query\":{\"bool\":{\"filter\":{\"term\":{\"recipient\":\"$recipient\"}}}}}"

# Envoi du document
msgContent=$(curl -s -X POST "$pod/message/$type/_search" -d "$document" | jq .hits.hits[]._source -c)

#Traitement des données
n=0
for i in $msgContent; do
    echo -e "=== $n ===\n"
    dataObj=($(jq -r '.issuer,.recipient,.nonce,.title,.content,.time' <<<"$i"))
    issuer="${dataObj[0]}"
    recipient="${dataObj[1]}"
    nonce=$(echo "${dataObj[2]}" | base58 -d | base64 -w 0)
    title="${dataObj[3]}"
    content="${dataObj[4]}"
    time="${dataObj[5]}"

    titleClear=$(./natools.py box-decrypt -p $issuer -f pubsec -k $dunikey -n $nonce -I 64 <<< "${title}")
    contentClear=$(./natools.py box-decrypt -p $issuer -f pubsec -k $dunikey -n $nonce -I 64 <<< "${content}")
    echo "$titleClear"
    echo "$contentClear"
    echo "========="
    ((n++))
#    echo "./natools.py box-decrypt -p $issuer -f pubsec -k $dunikey -n $nonce -I 64 <<< \"${title}\""
done

#echo "$msgContent" | jq

