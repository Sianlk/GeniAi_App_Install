# Wallet Monitoring
import wallet_api

def monitor_wallet():
    print("[INFO] Monitoring wallet for balance changes...")
    wallet_balance = wallet_api.get_balance()
    print(f"[DEBUG] Wallet balance: {wallet_balance}")
    return wallet_balance
