#!/usr/bin/env python3

import sys, re, os.path, json, ast
from termcolor import colored
from lib.natools import fmt, sign, get_privkey
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

PUBKEY_REGEX = "(?![OIl])[1-9A-Za-z]{42,45}"

class ListWallets:

    def __init__(self, node, brut, mbr, nonMbr, larf):
        self.mbr = mbr
        self.larf = larf
        self.nonMbr = nonMbr
        self.brut = brut
        # Define Duniter GVA node
        transport = AIOHTTPTransport(url=node)
        self.client = Client(transport=transport, fetch_schema_from_transport=True)

    def sendDoc(self):
        # Build wallets generation document
       
        queryBuild = gql(
            """
            {
                wallets(pagination: { cursor: null, ord: ASC, pageSize: 0 }) {
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                    edges {
                        node {
                            script
                            balance {
                                amount
                                base
                            }
                            idty {
                                isMember
                                username
                            }
                        }
                    }
                }
            }
        """)

        # Send wallets document
        try:
            queryResult = self.client.execute(queryBuild)
        except Exception as e:
            sys.stderr.write("Echec de récupération de la liste:\n" + str(e) + "\n")
            sys.exit(1)

        jsonBrut = queryResult['wallets']['edges']
        
        walletList = []
        for i, trans in enumerate(jsonBrut):
            dataWork = trans['node']
            if (self.mbr and (dataWork['idty'] == None or dataWork['idty']['isMember'] == False)): continue
            if (self.nonMbr and (dataWork['idty'] == None or dataWork['idty']['isMember'] == True)): continue
            if (self.larf and (dataWork['idty'] != None)): continue
            walletList.append({'pubkey': dataWork['script'],'balance': dataWork['balance']['amount'],'id': dataWork['idty']})

        if (self.brut):
            names = []
            for dataWork in walletList:
                names.append(dataWork["pubkey"])
            
            return "\n".join(names)
        else:
            return json.dumps(walletList, indent=2)
