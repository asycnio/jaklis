# Utilisation de la messagerie Cesium+/Gchange
## Réception/Envoi/Suppression de messages

## Installation

Linux:
```
bash setup.sh
```

Autre:
```
Débrouillez-vous.
```

## Utilisation

Renseignez le fichier userEnv.py (Généré lors de la première tentative d'execution, ou à copier depuis userEnv.py.template).

### Lecture des messages
```
./dialog.py read
```

_Options_:
```
-h, --help            show this help message and exit
-n NUMBER, --number NUMBER
                    Affiche les NUMBER derniers messages
-o, --outbox          Lit les messages envoyés
```

### Envoi de messages
```
./dialog.py send -d DESTINATAIRE
```

_Options_:
```
-h, --help            show this help message and exit
-d DESTINATAIRE, --destinataire DESTINATAIRE
                    Destinataire du message
-t TITRE, --titre TITRE
                    Titre du message à envoyer
-m MESSAGE, --message MESSAGE
                    Message à envoyer
-f FICHIER, --fichier FICHIER
                    Envoyer le message contenu dans le fichier 'FICHIER'
-o, --outbox          Envoi le message sur la boite d'envoi
```

### Suppression de messages
```
./dialog.py delete -i ID
```

_Options_:
```
-h, --help      show this help message and exit
-i ID, --id ID  ID du message à supprimer
-o, --outbox    Suppression d'un message envoyé
```
