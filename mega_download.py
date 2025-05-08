import os
from mega import Mega

# Mega login credentials
email = "empowermentemotive@gmail.com"
password = "Gucci1102#@"

# Login to Mega
mega = Mega()
m = mega.login(email, password)

# List available files and download .zip or 'genesis' files
files = m.get_files()
for f_id, f in files.items():
    name = f['a']['n']
    if name.endswith('.zip') or 'genesis' in name.lower():
        print(f"Downloading: {name}")
        m.download(f, dest_filename=f"./{name}")
        print("✅ Downloaded to UK-based VPS.")
