Ceci est un testeur simple pour l'envoi de messages Cesium +

# Utilisation

```
chmod u+x readmsg.sh sendmsg.sh deletemsg.sh
```
Par défaut utilise l'émetteur, le fichier de trousseau ainsi que le noeud Cesium+ indiqué dans le fichier `.env`.
Si non renseigné ni dans le fichier `.env` ni en argument de la commande, alors ils seront demandés interactivement.

## Lecture des messages
```
./readmsg.sh
```

_Options_:
```
    -r,--recipient <pubkey>	Uses <pubkey> as recipient of the messages.
    -k,--key <key>		Path <key> to the pubsec keychain file of the issuer.
    -n,--number <number>	Display the <number> lasts messages from Cesium (tail-like format)
    -o,--outbox			Read outbox messages instead of inbox
    -h,--help			Display this help
```

## Envoi de messages
```
./sendmsg.sh
```

_Options_:
```
    -t				Test mode: Uses the "test.txt" file as well as the same recipient as the sender.
    -f,--file <file>		Read the file <file> with title in first line and content in rest of the file for the message.
    -r,--recipient <pubkey>	Uses <pubkey> as recipient of the message.
    -i,--issuer <pubkey>	Uses <pubkey> as issuer of the message (Could be remove in future version by calculating pubkey from privatekey).
    -k,--key <key>		Path <key> to the pubsec keychain file of the issuer.
    -h,--help			Display this help
```

## Suppression de messages
```
./deletemsg.sh
```

_Options_:
```
    -id,--id <ID du message>	Delete the message with ID <id>.
    -i,--issuer <pubkey>	Uses <pubkey> as issuer of the message.
    -k,--key <key>		Path <key> to the pubsec keychain file of the issuer.
    -o,--outbox			Delete outbox messages instead of inbox
    -h,--help			Display this help
```
