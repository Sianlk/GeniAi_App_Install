# Stealth Mode Controller
import time
import wallet_api

STEALTH_THRESHOLD = 5000  # Stealth mode ends when wallet reaches 5k

def enable_stealth_mode():
    print("[INFO] Enabling stealth mode...")
    while True:
        wallet_balance = wallet_api.get_balance()
        print(f"[DEBUG] Wallet balance: {wallet_balance}")
        if wallet_balance >= STEALTH_THRESHOLD:
            print("[INFO] Stealth mode ends. Ready for live deployment.")
            break
        time.sleep(60)  # Check balance every minute

def is_stealth_mode_active():
    wallet_balance = wallet_api.get_balance()
    return wallet_balance < STEALTH_THRESHOLD
