#!/bin/bash

# ###
# Supprimer un message Cesium+
# ###

[[ ! -f .env ]] && cp .env.template .env
source .env

REGEX_PUBKEYS="[a-zA-Z0-9]{42,44}"

# Parse options
declare -a args=($@)
for ((i=0; i<${#args[*]}; ++i))
do
    case ${args[$i]} in
        -t|--test) file="test.txt"
            recipient=$issuer;;
		-o|--outbox) type=outbox;;
        -id|--id) id="${args[$i+1]}"
            [[ -z $id ]] && echo "Veuillez préciser un ID de message." && exit 1;;
        -i|--issuer) issuer="${args[$i+1]}"
            [[ -z $issuer ]] && echo "Veuillez préciser un émetteur." && exit 1;;
        -k|--key) dunikey="${args[$i+1]}"
            [[ -z $dunikey ]] && echo "Veuillez préciser un fichier de trousseau." && exit 1;;
        *) [[ "${args[$i]}" == "-"* ]] && echo "Option inconnue." && exit 1;;
    esac
done

if [[ -z $type ]]; then
    type="inbox"
fi
if [[ -z $id ]]; then
    read -p "ID de message: " ID
fi
if [[ -z $issuer ]]; then
    read -p "Émetteur: " issuer
fi
if [[ -z $dunikey ]]; then
    read -p "Fichier de trousseau: " dunikey
fi

[[ -z $(grep -Eo $REGEX_PUBKEYS <<<$issuer) ]] && echo "Le format de la clé publique de l'émetteur est invalide." && exit 1

times=$(date -u +'%s')

# Fabrication du hash
hash="{\"version\":2,\"index\":\"message\",\"type\":\"$type\",\"id\":\"$id\",\"issuer\":\"$issuer\",\"time\":$times}"
hash=$(echo -n "$hash" | sha256sum | cut -d ' ' -f1 | awk '{ print toupper($0) }')

# Fabrication de la signature
signature=$(echo -n "$hash" | ./natools.py sign -f pubsec -k $dunikey --noinc -O 64)

# Affichage du JSON final
echo "{
    \"version\": 2,
    \"index\": \"message\",
    \"type\": \"$type\",
    \"id\": \"$id\",
    \"issuer\": \"$issuer\",
    \"time\": $times,
    \"hash\": \"$hash\",
    \"signature\": \"$signature\"
}"

# Envoi du document
curl -X POST "$pod/history/delete" -d "{\"version\":2,\"index\":\"message\",\"type\":\"$type\",\"id\":\"$id\",\"issuer\":\"$issuer\",\"time\":$times,\"hash\":\"$hash\",\"signature\":\"$signature\"}"
