# Python Meraki Lab Automation

Automated Cisco Meraki network provisioning using the Python SDK.

This tool creates new Meraki organizations and networks, assigns devices, and sets default configurations — ideal for labs or ephemeral testing setups.

---

## 🚀 Features

- ✅ Creates new orgs and networks with incrementing names
- 🔐 Prompts for manual unclaiming of devices before reuse
- 🧹 Optionally removes devices from previous networks (`--destroy`)
- 📍 Sets addresses and places devices on the map
- 📦 Logs each deployment with a custom filename
- ⚙️ Uses `pyproject.toml` + `uv` for dependency management

---

## 🛠️ Usage

### Requirements

- Python 3.10+
- Cisco Meraki API key
- Devices claimed to your dashboard account
- `uv` installed as the Python package manager

### Setup

```bash
uv venv
source .venv/bin/activate
uv pip install -r uv.lock
```

## Run
```
python main.py
```

### Options

	•	--config: Specify a custom config file (default: config.json)
	•	--destroy: Remove devices from the previous network before reuse

## Structure

.
├── config.json               # Device and naming config
├── main.py                  # Entry point
├── meraki_sdk/              # Modular SDK wrappers
│   ├── auth.py
│   ├── devices.py
│   ├── network.py
│   ├── org.py
│   └── logging_config.py
├── logs/                    # Deployment logs
├── pyproject.toml           # Dependency metadata
└── uv.lock                  # Frozen lockfile

## Roadmap

	•	🔁 Rename old orgs to "DEAD - To be deleted"
	•	🌍 Automate Vision Portal video wall setup
	•	📖 Add MkDocs documentation
	•	🧪 Add runtime validation (e.g., Pydantic)
	•	🧩 Extend config templating

🙌 Credits

Hacked together by Lukeoson using the Meraki Python SDK.