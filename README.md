Ceci est un testeur simple pour l'envoi de messages Cesium +

# Utilisation

```
chmod u+x sendmsg.sh
./sendmsg.sh
```

## Options
./sendmsg.sh
    Par défaut, demandez le titre, le contenu et le destinataire en mode interactif.

Options:
    -t			Mode test: Utilise le fichier "test.txt" ainsi que le même destinataire que l'émetteur.
    -f <file>	Lit le fichier <file> avec le titre en première ligne et le contenu dans le reste du fichier pour le message.
    -r <pubkey>	Utilise <pubkey> comme destinataire du message.
    -i <pubkey>	Utilise <pubkey> comme émetteur du message.
    -k <key>	Chemin <key> vers le fichier de trousseau PubSec de l'émetteur.
