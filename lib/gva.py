import sys, re
from lib.natools import get_privkey
from lib.gvaPay import Transaction, PUBKEY_REGEX
from lib.gvaHistory import History
from lib.gvaBalance import Balance

class GvaApi():
    def __init__(self, dunikey, node, pubkey):
        self.dunikey = dunikey
        self.node = node
        self.pubkey = get_privkey(dunikey, "pubsec").pubkey
        if pubkey:
            self.destPubkey = pubkey
        else:
            self.destPubkey = self.pubkey

        try:
            if not re.match(PUBKEY_REGEX, self.pubkey) or len(self.pubkey) > 45:
                raise ValueError("La clé publique n'est pas au bon format.")
        except:
            sys.stderr.write("La clé publique n'est pas au bon format.\n")
            raise

        try:
            if not re.match(PUBKEY_REGEX, self.destPubkey) or len(self.destPubkey) > 45:
                raise ValueError("La clé publique n'est pas au bon format.")
        except:
            sys.stderr.write("La clé publique n'est pas au bon format.\n")
            raise

    #################### Payments ####################

    def pay(self, amount, comment, mempool, verbose):
        gva = Transaction(self.dunikey, self.node, self.destPubkey, amount, comment, mempool, verbose)
        gva.genDoc()
        gva.checkTXDoc()
        gva.signDoc()
        return gva.sendTXDoc()

    def history(self, isJSON=False, noColors=False):
        gva = History(self.dunikey, self.node, self.destPubkey)
        gva.sendDoc()
        transList = gva.parseHistory()

        if isJSON:
            transJson = gva.jsonHistory(transList)
            print(transJson)
        else:
            gva.printHistory(transList, noColors)
    
    def balance(self, useMempool):
        gva = Balance(self.dunikey, self.node, self.destPubkey, useMempool)
        balanceValue = gva.sendDoc()
        print(balanceValue)
