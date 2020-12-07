import string, random, base64
from lib.cesiumCommon import CesiumCommon
from lib.messaging import ReadFromCesium, SendToCesium, DeleteFromCesium

class CesiumPlus(CesiumCommon):
    def read(self, nbrMsg, outbox, isJSON):
        readCesium = ReadFromCesium(self.dunikey,  self.pod)
        jsonMsg = readCesium.sendDocument(nbrMsg, outbox)
        if isJSON:
            jsonFormat = readCesium.jsonMessages(jsonMsg, nbrMsg, outbox)
            print(jsonFormat)
        else:
            readCesium.readMessages(jsonMsg, nbrMsg, outbox)

    def send(self, title, msg, recipient, outbox):
        sendCesium = SendToCesium(self.dunikey, self.pod)
        sendCesium.recipient = recipient

        # Generate pseudo-random nonce
        nonce=[]
        for _ in range(32):
            nonce.append(random.choice(string.ascii_letters + string.digits))
        sendCesium.nonce = base64.b64decode(''.join(nonce))

        finalDoc = sendCesium.configDoc(sendCesium.encryptMsg(title), sendCesium.encryptMsg(msg))       # Configure JSON document to send
        sendCesium.sendDocument(finalDoc, outbox)                                                       # Send final signed document

    def delete(self, idsMsgList, outbox):
        deleteCesium = DeleteFromCesium(self.dunikey,  self.pod)
        # deleteCesium.issuer = recipient
        for idMsg in idsMsgList:
            finalDoc = deleteCesium.configDoc(idMsg, outbox)
            deleteCesium.sendDocument(finalDoc, idMsg)
