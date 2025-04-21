# Meta Wallet Integration
import meta_wallet_api

META_WALLET_ADDRESS = "0x15111d3a83a74e73bd0969ecb743d70d4e51d585"

def integrate_meta_wallet(user):
    print("Integrating Meta Wallet for user...")
    wallet = meta_wallet_api.create_wallet(user, META_WALLET_ADDRESS)
    print(f"Meta Wallet successfully integrated with address: {META_WALLET_ADDRESS}")
    return wallet
