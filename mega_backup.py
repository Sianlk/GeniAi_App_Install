from mega import Mega  
import os  
import datetime  

mega = Mega()
email = os.environ.get('MEGA_EMAIL')
password = os.environ.get('MEGA_PASSWORD')
m = mega.login(email, password)

backup_dir = '/var/www/geniqx'
archive_name = f"geniqx_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

os.system(f"zip -r /tmp/{archive_name} {backup_dir}")
uploaded_file = m.upload(f"/tmp/{archive_name}")

print("✅ Uploaded Backup to Mega.nz:", uploaded_file)
