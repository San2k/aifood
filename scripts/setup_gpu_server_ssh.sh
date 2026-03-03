#!/bin/bash
# Script to add SSH key to GPU server 199.247.7.186

echo "=== Adding SSH key to GPU server 199.247.7.186 ==="
echo ""
echo "Public key to add:"
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJc2nrIOC/RKyTo43wMcTXPc/mWU/Di95IzLDbGdo8B7 sandro@SP-MacBook-Pro.local"
echo ""
echo "Steps:"
echo "1. SSH to the GPU server: ssh root@199.247.7.186"
echo "2. Run: echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJc2nrIOC/RKyTo43wMcTXPc/mWU/Di95IzLDbGdo8B7 sandro@SP-MacBook-Pro.local' >> ~/.ssh/authorized_keys"
echo "3. Run: chmod 600 ~/.ssh/authorized_keys"
echo ""
echo "Or copy-paste this one-liner after SSHing to the server:"
echo ""
echo "mkdir -p ~/.ssh && echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJc2nrIOC/RKyTo43wMcTXPc/mWU/Di95IzLDbGdo8B7 sandro@SP-MacBook-Pro.local' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && chmod 700 ~/.ssh"
