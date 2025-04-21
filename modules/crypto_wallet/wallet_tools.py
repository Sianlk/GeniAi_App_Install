# Crypto Wallet Module
import crypto_api

def setup_crypto_wallet(user):
    print("Setting up crypto wallet...")
    wallet = crypto_api.create_wallet(user)
    return wallet
