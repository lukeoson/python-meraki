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
- 🔐 Sets firewall rules (outbound) via config
- 🛰️ Supports VPN configuration (AutoVPN + IPsec peers) - Coming Soon. 
- 🧠 Dynamic runtime state tracking for org/network IDs
- 🧾 Deployment summaries saved as JSON and human-readable logs
- 🧹 Supports device removal from old networks (`--destroy`)
- 📝 Saves structured logs and summaries to `logs/summary_log/`
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
├── config/                        # All configuration files, separated by purpose
│   ├── common/                    # Reusable config fragments shared across projects
│   │   ├── exclusion_rules.yaml   # Rules to exclude devices or items from config
│   │   ├── firewall/              # MX firewall rule configs
│   │   ├── ports/                 # MX port configurations
│   │   ├── routes/                # Static route definitions
│   │   ├── vlans.yaml             # Default VLAN definitions
│   │   └── wireless/              # Wireless SSID and settings configs
│   ├── defaults.yaml              # Global defaults applied to all networks/orgs
│   ├── devices/                   # Device inventory files
│   ├── manifest.yaml              # Primary project manifest (declares orgs/networks)
│   └── projects/                  # Project-specific overrides
│       └── percy_street/          # Project folder with per-network overrides
├── logs/                          # Logging output from deployments
│   ├── custom_logs/               # User-defined log entries and custom flows
│   ├── meraki_logs/               # Raw logs from Meraki SDK/API interactions
│   └── summary_log/               # Human-readable and JSON deployment summaries
├── state/                         # State tracking for intended vs actual deployments
│   ├── actual_state/              # (planned) Actual state pulled from live API
│   ├── intended_state/            # JSON dumps of what was intended per deployment
│   └── runtime.json               # Captures org/network IDs during each run
├── meraki_sdk/                    # Core automation logic for Meraki provisioning
│   ├── auth.py                    # API key setup and auth session management
│   ├── device.py                  # Core device management helpers
│   ├── org.py                     # Functions to create/manage Meraki orgs
│   ├── network.py                 # Common utilities for Meraki networks
│   ├── logging_config.py          # Custom logger setup
│   ├── devices/                   # Device setup modules (naming, port configs)
│   ├── network/                   # Modules for logical network constructs
│   │   ├── setup_network.py       # Main entrypoint to apply network settings
│   │   ├── vlans/                 # VLAN logic: exclusions, fixed IPs, DHCP
│   │   ├── ports/                 # MX port assignment logic
│   │   ├── routes/                # Static route config
│   │   ├── firewall/              # Firewall rule configuration
│   │   ├── vpn/                   # VPN configuration (AutoVPN, IPsec)
│   │   └── wireless/              # Wireless config logic
├── utils/                         # Utility modules for state handling, logging, testing
│   ├── logging/                   # Custom logging logic
│   │   ├── config.py              # Logging config utilities
│   │   └── summary.py             # Structured deployment summaries
│   ├── state/                     # Runtime and config state handling
│   │   ├── config.py              # Intended/actual state helpers
│   │   └── runtime.py             # Persists runtime org/network metadata
│   └── tests/                     # Unit test logic (WIP)
├── backend/                       # Backend interface abstraction (local, NetBox etc.)
├── ipam/                          # IPAM logic for subnet allocation
├── docs/                          # Documentation and architecture notes
├── config_loader.py               # Loads YAML and prepares config structure
├── config_resolver.py             # Merges and resolves project config
├── main.py                        # CLI entrypoint and workflow orchestrator
├── pyproject.toml                 # Project metadata and dependencies
├── uv.lock                        # Locked dependency versions for reproducible installs
├── pytest.ini                     # Pytest configuration
└── README.md                      # This file
```

## 🛤️ Roadmap
- 🛰️ Expand VPN support.
- ♻️ Idempotence
- 📖 Documentation
- 🌐 More Modules
- 🧠 Bigger Better Stronger


Built with Python, the Meraki SDK.