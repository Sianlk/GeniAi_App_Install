#!/usr/bin/bash

# Update and install basic packages
apt update -y && pkg install curl proot tar -y

# Download and install Ubuntu 20
curl https://raw.githubusercontent.com/AndronixApp/AndronixOrigin/master/Installer/Ubuntu20/ubuntu20.sh | bash

# Create a VSCODE launcher script
echo '#!/usr/bin/bash' > vscode.sh
echo './start-ubuntu20.sh && ./code-server-3.8.1-linux-arm64/bin/code-server' >> vscode.sh
chmod +x vscode.sh

# Create a VSCode installer script for inside Ubuntu
echo '#!/usr/bin/bash
apt update -y && apt upgrade -y
apt install wget -y
wget https://github.com/cdr/code-server/releases/download/v3.8.1/code-server-3.8.1-linux-arm64.tar.gz
tar -xvf code-server-3.8.1-linux-arm64.tar.gz
rm code-server-3.8.1-linux-arm64.tar.gz
mkdir -p ~/.config/code-server
echo "bind-addr: 127.0.0.1:8080" > ~/.config/code-server/config.yaml
echo "auth: password" >> ~/.config/code-server/config.yaml
echo "password: 1" >> ~/.config/code-server/config.yaml
echo "cert: false" >> ~/.config/code-server/config.yaml
' > vscode-install.sh
chmod +x vscode-install.sh

echo "Ubuntu installed. Now run ./start-ubuntu20.sh and inside Ubuntu terminal run ./vscode-install.sh"
