#! /usr/bin/python3

import sys
from base58 import b58decode
from base64 import b64decode
from libnacl import crypto_sign_ed25519_sk_to_curve25519 as private_sign2crypt
from libnacl import crypto_sign_ed25519_pk_to_curve25519 as public_sign2crypt
from libnacl.sign import Signer, Verifier
from libnacl.public import SecretKey, PublicKey, Box

sender_pub = sys.argv[1]
recip_seed = sys.argv[2]
nonce = sys.argv[3]
title = sys.argv[4]
content = sys.argv[5]

signer = Signer(b58decode(recip_seed))
sk = SecretKey(private_sign2crypt(signer.sk))

verifier = Verifier(b58decode(sender_pub).hex())
pk = PublicKey(public_sign2crypt(verifier.vk))

box = Box(sk.sk, pk.pk)

print("Objet: " + box.decrypt(b64decode(nonce) + b64decode(title)).decode('utf-8'))
print("\n" + box.decrypt(b64decode(nonce) + b64decode(content)).decode('utf-8'))

