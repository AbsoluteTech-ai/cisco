

## <code copy>Automated Networking</code>

Decentralised Repositories via a python REPL CI/CD called RADKit using rotating APIs

## Installation

Install RADKit from https://radkit.cisco.com/downloads/release/

Once devices added and verified with **service.inventory**

**which genie**

**which python**

**python3 -m venv .venv**

**source /home/#/.local/radkit/versions/1.#/venv/bin/activate**

**radkit-service run** (this will show real-time status)

## Usage


**cd ~/.local/radkit/versions/1.#/venv/bin**

```
$ radkit-client script rk-update-https.py
```
```
$ radkit-client script rk-update-sshciphers.py
```

**deactivate**
