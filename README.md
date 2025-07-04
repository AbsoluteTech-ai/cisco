

## <code copy>Automated Networking</code>

Decentralised Repositories via a python REPL CI/CD called RADKit using rotating APIs

![RADKitFlow2](https://iili.io/FYrAG9I.md.png)

## Installation

Install RADKit from https://radkit.cisco.com/downloads/release/

Once devices added and verified with **service.inventory**

**which genie**

**which python**

**python3 -m venv .venv**

**source /home/#/.local/radkit/versions/1.#/venv/bin/activate**

**radkit-service run** (this will show real-time status)

![RADKit Flow](https://iili.io/FYrC0iB.md.png)

## Usage


**cd ~/.local/radkit/versions/1.#/venv/bin**

```
$ radkit-client script rk-update-https.py
```
```
$ radkit-client script rk-update-sshciphers.py
```

**deactivate**

## Can also us used directly as IOx App on Cisco Devices with USB guestshell/docker

![IOX-App1](https://iili.io/FYrGCYu.md.jpg)

```
$ conf t
iox 
app-hosting appid guestshell 
app-vnic gateway# virtualportgroup # guest-interface #
  guest-ipaddress # netmask #
app-default-gateway # guest-interface #

app-resource profile custom
cpu 1000
memory 384
persist-disk 3
exit
name-server0 #

interface VirtualPortGroup#
ip address # #
ip nat inside 
interface #
ip nat outside 
end

ip nat inside source static tcp # 8081 # 8081 no-payload extendable stateless

guestshell enable
guestshell portforwarding add table-entry RADKIT service tcp source-port 8081 destination-port 8081
(only for docker via mgmt)
guestshell run bash

ls -ltr
chmod +x cisco_radkit_1.8.5_linux_x86_64.sh 

./cisco_radkit_1.8.5_linux_x86_64.sh -keep

Verify RADKit & BOOTSTRAP to create a superadmin pw and initiate RK DB

radkit-service --version
/home/guestshell/.local/bin/radkit-service bootstrap

systemctl enable radkit

show iox-service
systemctl start radkit

```