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
- 🛣️ Creates static routes`
- 🔐 Sets firewall rules (outbound) via config
- 🛰️ Supports VPN configuration (AutoVPN + IPsec peers)
- 🧠 Dynamic runtime state tracking for org/network IDs
- 🧾 Deployment summaries saved as JSON and human-readable logs
- 🧹 Supports device removal from old networks (`--destroy`)
- 📝 Saves structured logs and summaries to `logs/summary_log/
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
│   ├── common/
│   │   ├── exclusion_rules.yaml
│   │   ├── firewall/
│   │   ├── ports/
│   │   ├── routes/
│   │   ├── vlans.yaml
│   │   └── wireless/
│   ├── defaults.yaml
│   ├── devices/
│   ├── manifest.yaml
│   └── projects/
│       └── percy_street/
├── logs/
│   ├── custom_logs/
│   ├── meraki_logs/
│   └── summary_log/
├── state/
│   ├── actual_state/
│   ├── intended_state/
│   └── runtime.json
├── meraki_sdk/
│   ├── auth.py
│   ├── device.py
│   ├── org.py
│   ├── network.py
│   ├── logging_config.py
│   ├── devices/
│   │   └── setup_devices.py
│   ├── network/
│   │   ├── setup_network.py
│   │   ├── vlans/
│   │   │   ├── mx.py
│   │   │   ├── exclusions.py
│   │   │   └── fixed_assignments.py
│   │   ├── ports/
│   │   │   └── mx_ports.py
│   │   ├── routing/
│   │   │   └── static.py
│   │   └── firewall/
│   │   │   └── firewall.py
├── main.py
├── config_loader.py
├── pyproject.toml
├── uv.lock
└── tests/
```

## 🛤️ Roadmap
- 🛰️ Expand VPN support.
- ♻️ Idempotence
- 📖 Documentation
- 🌐 More Modules
- 🧠 Bigger Better Stronger


Built with Python, the Meraki SDK.