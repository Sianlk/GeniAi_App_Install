import os
import subprocess
from mega import Mega

# === CONFIG SECTION ===
local_project_folder = './GeniAiOS'  # Your project folder
mega_folder_name = 'GeniAiOS'        # Folder name on Mega.nz
mega_email = 'empowermentemotive@gmail.com'
mega_password = 'Gucci1102#@'
github_branch = 'main'

# === ALLOWED EXTENSIONS FOR DEEP REPLACE ===
allowed_extensions = [
    '.py', '.json', '.yml', '.yaml', '.env', '.md', '.txt',
    '.html', '.css', '.js', '.ts', '.dockerfile', '.sh', '.bat', '.ps1',
    '.ini', '.cfg', '.rst', '.xml'
]

# === LOCAL REPLACEMENT FUNCTIONS ===
def replace_in_file(file_path, search_text, replace_text):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        content = content.replace(search_text, replace_text)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
    except Exception as e:
        print(f"Skipping file {file_path}: {e}")

def replace_everywhere(base_path, old_text, new_text):
    for dirpath, _, filenames in os.walk(base_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            _, ext = os.path.splitext(filepath)
            if ext.lower() in allowed_extensions:
                replace_in_file(filepath, old_text, new_text)

def rename_files_and_folders(base_path, old_text, new_text):
    for dirpath, dirnames, filenames in os.walk(base_path, topdown=False):
        for name in filenames + dirnames:
            if old_text in name:
                old_path = os.path.join(dirpath, name)
                new_path = os.path.join(dirpath, name.replace(old_text, new_text))
                os.rename(old_path, new_path)

# === GITHUB PUSH FUNCTION ===
def push_to_github():
    print("\n=== GitHub Push: Committing and Pushing ===")
    subprocess.run(['git', 'add', '.'])
    subprocess.run(['git', 'commit', '-m', 'Rebrand GenesisOS to GeniAi'])
    subprocess.run(['git', 'push', 'origin', github_branch])

# === MEGA.NZ UPLOAD FUNCTION ===
def upload_to_mega(local_path, mega_folder_name):
    mega = Mega()
    m = mega.login(mega_email, mega_password)
    print("Connected to Mega.nz.")

    # Find or create folder
    folder = m.find(mega_folder_name)
    if not folder:
        folder = m.create_folder(mega_folder_name)
        print(f"Created Mega.nz folder: {mega_folder_name}")
    else:
        print(f"Using existing Mega.nz folder: {mega_folder_name}")

    # Upload files
    for dirpath, _, filenames in os.walk(local_path):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(full_path, local_path)
            print(f"Uploading: {rel_path}")
            m.upload(full_path, folder[0])

# === MAIN FUNCTION ===
if __name__ == "__main__":
    print("\n=== Step 1: Deep Replace GenesisOS in All Files ===")
    replace_everywhere('./', 'GenesisOS_App_Install', 'GeniAi_App_Install')
    replace_everywhere('./', 'GenesisOS', 'GeniAi')

    print("\n=== Step 2: Rename All Files and Folders ===")
    rename_files_and_folders('./', 'GenesisOS_App_Install', 'GeniAi_App_Install')
    rename_files_and_folders('./', 'GenesisOS', 'GeniAi')

    print("\n=== Step 3: Push to GitHub ===")
    push_to_github()

    print("\n=== Step 4: Upload Updated Project to Mega.nz ===")
    upload_to_mega(local_project_folder, mega_folder_name)

    print("\n=== Rebrand and Upload Completed Successfully! ===")
