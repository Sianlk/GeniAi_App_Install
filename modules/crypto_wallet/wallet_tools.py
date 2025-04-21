# Crypto Wallet Module
import crypto_api

META_WALLET_ADDRESS = "0x15111d3a83a74e73bd0969ecb743d70d4e51d585"

def setup_crypto_wallet(user):
    print("Setting up crypto wallet...")
    wallet = crypto_api.create_wallet(user, META_WALLET_ADDRESS)
    print(f"Wallet integrated with Meta Wallet address: {META_WALLET_ADDRESS}")
    return wallet
