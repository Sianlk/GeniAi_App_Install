# VoIP Tools
import voip_api

def setup_voip_services(user):
    print("Setting up VoIP services...")
    voip_account = voip_api.create_account(user)
    return voip_account
