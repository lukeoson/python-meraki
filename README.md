# Python Meraki Lab Automation

Automated Cisco Meraki network provisioning using the Python SDK.

This tool creates new Meraki organizations and networks, claims devices, sets network configuration and produces full deployment logs — ideal for lab or ephemeral testing environments.

---

## 🚀 Features

- 🏢 Creates new Meraki organizations and networks with incrementing names
- 📦 Claims and names devices using a structured naming convention
- 📍 Sets device addresses and places devices on maps
- 🌐 Configures VLANs, DHCP, and reserved IP assignments
- 🔌 Configures MX ports after VLANs are enabled
- 🛣️ Creates static routes
- 🧹 Supports device removal from old networks (`--destroy`)
- 📝 Saves full deployment summaries (named after the deployment number)
- ⚙️ Modern dependency management using `pyproject.toml` + `uv`
- 🧩 Modular code structure, fully separated between devices and logical network constructs

---

## 🛠️ Requirements

- Python 3.10+
- Cisco Meraki API Key
- Devices already claimable via API
- [`uv`](https://github.com/astral-sh/uv) installed

---

## 📦 Installation

```bash
uv venv
source .venv/bin/activate
uv pip install -r uv.lock
```

## 🚀 Running the Tool

```zsh
python main.py
```

### Options


| Option     | Description                                      |
|------------|--------------------------------------------------|
| `--destroy` | Remove devices from their previous network before reuse |
| `--config`  | (future) Load an alternate config file |

## 🗂️ Project Structure
```
.
├── config/
│   ├── base.json
│   ├── devices.json
│   ├── exclusion_rules.yaml
│   ├── fixed_ip_assignments.yaml
│   ├── ports/
│   │   └── mx_ports.json
│   ├── static_routes.json
│   └── vlans.json
├── logs/
│   ├── custom_logs/
│   ├── meraki_logs/
│   └── summary_log/
├── meraki_sdk/
│   ├── auth.py
│   ├── device.py
│   ├── org.py
│   ├── network.py
│   ├── logging_config.py
│   ├── devices/
│   │   └── setup_devices.py
│   ├── network_constructs/
│   │   ├── setup_network_constructs.py
│   │   ├── vlans/
│   │   │   ├── mx.py
│   │   │   ├── exclusions.py
│   │   │   └── fixed_assignments.py
│   │   ├── ports/
│   │   │   └── mx_ports.py
│   │   ├── routing/
│   │   │   └── static.py
│   │   └── vpn.py
├── main.py
├── config_loader.py
├── pyproject.toml
├── uv.lock
└── tests/
```

## 🛤️ Roadmap
- 🔥 Add Firewall rules automation
- 📖 MkDocs site documentation
- 🌐 Full VPN/OSPF/BGP configuration modules
- 🧠 Smarter device exclusion and pre-checks

## 🙌 Credits

Built by Lukeoson,
with Python, the Meraki SDK. Hacky!