Automated Networking

Decentralised Repositories via a python REPL called RADkit

Install RADkit from https://radkit.cisco.com/downloads/release/

Once devices added and verified with service.inventory

which genie

which python

python3 -m venv .venv

source /home/svc_radkit_su/.local/radkit/versions/#/venv/bin/activate 

radkit-service run (this will show real-time status)

Can execute scripts outside of REPL with scripts in seperate window 
cd ~/.local/radkit/versions/#/venv/bin

radkit-client script rk-update-https.py

radkit-client script rk-update-ssh&ciphers.py
