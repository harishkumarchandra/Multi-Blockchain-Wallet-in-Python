import subprocess
import json
from constants import *
import os
from eth_account import Account
from bit import PrivateKeyTestnet
from web3 import Web3
from bit.network import NetworkAPI
from web3.middleware import geth_poa_middleware

w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

def derive_wallets():

    mnemonic = os.getenv('MNEMONIC', 'fallback mnemonic')
    coins = [ETH, BTCTEST]
    wallet = {}

    for coin in coins:
        command = f'php derive -g --mnemonic="{mnemonic}" --cols=path,address,privkey,pubkey --coin={coin} --format=json --numderive=3'
        p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        (output, error) = p.communicate()
        p_status = p.wait()
        keys = json.loads(output)
        wallet[coin] = keys

    return wallet


coins = derive_wallets()

def priv_key_to_account(coin, priv_key):

    if(coin == 'eth'):
        return Account.privateKeyToAccount(priv_key)
    elif(coin == 'btc-test'):
        return PrivateKeyTestnet(priv_key)


def create_tx(coin, account, to, amount):

    if(coin == 'eth'):
        gas_estimate = w3.eth.estimateGas(
            {'from': account.address, 'to': to, 'value': amount}
        )
        return {
            'from': account.address,
            'to': to,
            'value': amount,
            'gasPrice': w3.eth.gasPrice,
            'gas': gas_estimate,
            'nonce': w3.eth.getTransactionCount(account.address)
        }
    elif(coin == 'btc-test'):
        return PrivateKeyTestnet.prepare_transaction(account.address, [(to, amount, BTC)])

def send_txn(coin, account, to, amount):
    raw_tx = create_tx(coin, account, to, amount)
    signed = account.sign_transaction(raw_tx)
    if(coin == 'eth'):
        return w3.eth.sendRawTransaction(signed.rawTransaction)
    elif(coin == 'btc-test'):
        return NetworkAPI.broadcast_tx_testnet(signed)
