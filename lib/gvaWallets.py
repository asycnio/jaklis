#!/usr/bin/env python3

import sys, re, os.path, json, ast
from termcolor import colored
from lib.natools import fmt, sign, get_privkey
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

PUBKEY_REGEX = "(?![OIl])[1-9A-Za-z]{42,45}"

class ListWallets:

    def __init__(self, node, getBalance, brut):
        self.getBalance = getBalance
        self.brut = brut
        # Define Duniter GVA node
        transport = AIOHTTPTransport(url=node)
        self.client = Client(transport=transport, fetch_schema_from_transport=True)

    def sendDoc(self, getBalance=True, brut=False):
        # Build wallets generation document
       
        queryBuild = gql(
            """
            {
                wallets(pagination: { cursor: "1NiFHXUQDVNXuKE54Q8SdQRWmtKPVtMqWBSb8d8VkiS", ord: ASC, pageSize: 0 }) {
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
        if (brut):
            names = []
            for dictionary in jsonBrut:
                dataWork = dictionary['node']
                if "script" in dataWork:
                    names.append(dataWork["script"])
            
            return names
        else:
            for i, trans in enumerate(jsonBrut):
                dataWork = trans['node']
                walletList.append(i)
                walletList[i] = {}
                walletList[i]['pubkey'] = dataWork['script']
                walletList[i]['id'] = dataWork['idty']            

            return json.dumps(walletList, indent=2)
