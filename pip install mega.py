import os
from mega import Mega

# === CONFIG ===
local_folder = './GeniAiOS'  # <-- your new renamed local folder
mega_folder = 'GeniAiOS'     # <-- where you want it uploaded on Mega.nz
mega_email = 'your-email@example.com'  # <-- your Mega.nz email
mega_password = 'your-password'        # <-- your Mega.nz password

# === LOCAL REPLACEMENT FUNCTION ===
def replace_in_file(file_path, search_text, replace_text):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    content = content.replace(search_text, replace_text)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def replace_everywhere(base_path, old_text, new_text):
    for dirpath, dirnames, filenames in os.walk(base_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                replace_in_file(filepath, old_text, new_text)
            except:
                print(f"Skipping non-text file: {filepath}")

# === MEGA.NZ UPLOAD FUNCTION ===
def upload_to_mega(local_path, mega_folder_name):
    mega = Mega()
    m = mega.login(mega_email, mega_password)
    
    # Optionally create a folder
    folder = m.find(mega_folder_name)
    if not folder:
        folder = m.create_folder(mega_folder_name)
    
    # Upload all files
    for dirpath, dirnames, filenames in os.walk(local_path):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(full_path, local_path)
            print(f"Uploading {rel_path}...")
            m.upload(full_path, folder[0])  # Folder ID

# === MAIN FUNCTION ===
if __name__ == "__main__":
    print("=== Updating Local Files ===")
    replace_everywhere('./', 'GenesisOS', 'GeniAi')
    replace_everywhere('./', 'GenesisOS_App_Install', 'GeniAi_App_Install')

    print("=== Uploading Updated Files to Mega.nz ===")
    upload_to_mega(local_folder, mega_folder)
    
    print("=== Done! ===")
