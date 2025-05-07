# 🧠 Meraki Automation Framework — Architecture Overview

## 📌 Design Philosophy

> **Declarative config in YAML, logic in Python.**
> The manifest defines intent. Python interprets and applies it.

---

## 🧱 System Structure

The automation stack is built on three key abstraction layers:

| Layer                     | Role                                              | Examples                                              |
| ------------------------- | ------------------------------------------------- | ----------------------------------------------------- |
| **Manifest + YAML**       | User-facing configuration describing the intent   | `manifest.yaml`, `defaults.yaml`                      |
| **Loader + Resolver**     | Load, merge, and resolve configs from all sources | `config_loader.py`, `config_resolver.py`              |
| **State + Runtime**        | Track ephemeral IDs for current deployment       | `runtime.py`, `runtime.json`                          |
| **Setup + Logic Modules** | Apply resolved config via SDK calls               | `setup_network.py`, `network/wireless/mx_wireless.py` |

---

## 🔧 Adding a New Feature (e.g., Wireless, VPN, etc.)

### 1. **Update `manifest.yaml`**

Declare the feature under `config:` inside the appropriate network.

```yaml
config:
  wireless: common/wireless/mx_wireless.yaml
```

### 2. **Update `defaults.yaml`** *(Optional)*

Add fallback values for networks that don't explicitly override this.

```yaml
wireless: common/wireless/default.yaml
```

### 3. **Add Shared Config Under `common/`**

Shared YAML goes in `common/{feature}/`. Use clear naming.

### 4. **Update Project-Specific Configs** *(Optional)*

If the feature needs per-project customization.

### 5. **Update `config_loader.py`**

Usually generic—only touch if custom parsing is required.

### 6. **Update `config_resolver.py`**

Ensure correct fallback logic is applied.

```python
network_config.get("wireless", default_config.get("wireless"))
```

### 7. **Update `setup_devices.py`** *(Device-level logic only)*

For configs like device names, fixed IPs, sensor bindings.

### 8. **Update `setup_network.py`** *(Network-level logic)*

Call the new logic conditionally:

```python
if "wireless" in config:
    apply_mx_wireless_settings(dashboard, network_id, config["wireless"])
```

### 9. **Write Logic Module**

Under the appropriate path, e.g.:

```python
# network/wireless/mx_wireless.py
def apply_mx_wireless_settings(dashboard, network_id, config: dict):
    ...
```

### 10. **Update `main.py`** *(Optional)*

Only if adding CLI flags or top-level testing.

### 🧠 Runtime State Tracking

As part of each deployment, a file is created at `state/runtime.json` to store ephemeral values like `org_id` and `network_id`.

This allows:
- Debugging and inspection of Meraki object IDs
- Use of verified IDs across modules (e.g., VPN configs, device mapping)
- Clean reset on next deployment (the file is overwritten each time)

These values are written during the deployment flow inside `main.py` via:
```python
from utils.state.runtime import save_runtime_state
```

And can be accessed on demand with:
```python
from utils.state.runtime import load_runtime_state
```

> Note: This is not long-term state — it reflects *only* the current run.

---

## 📂 Example Directory Layout

```
config/
├── manifest.yaml
├── defaults.yaml
├── common/
│   └── wireless/
│       └── mx_wireless.yaml
├── devices/
│   └── devices.yaml
├── projects/
│   └── percy_street/
│       ├── fixed_ip_assignments.yaml
│       └── vpn/
│           ├── autovpn.yaml
│           └── ipsec_peers.yaml
logs/
└── summary_log/
    └── summary-<org>.log
state/
├── runtime.json
└── runtime.py
src/
├── setup_network.py
├── network/
│   └── wireless/
│       └── mx_wireless.py
├── config_loader.py
├── config_resolver.py
main.py
```

---

## 🔁 Flow Summary

```yaml
manifest.yaml ──▶ config_loader.py ──▶ config_resolver.py
                                      │
                                      ▼
          ┌──────────────┐       ┌───────────────┐
          │ setup_devices.py ├─▶ │  setup_network.py ├──▶ (feature modules)
          └──────────────┘       └───────────────┘
                                      │
                                      ▼
                      ┌──────────────┐
                      │ runtime.py   │  ← store ephemeral state
                      └──────────────┘
                                      │
                                      ▼
                      ┌──────────────┐
                      │ summary.py   │  ← log summary + .json state
                      └──────────────┘
```

---

## 📎 Naming Conventions

* Use lowercase with underscores for slugs and filenames.
* Place shared configs in `common/{feature}/`
* Place logic modules in `network/{feature}/` or `device/{feature}/`

---

## 🔒 Future-Proofing

Every new feature should:

* Be toggleable via `manifest.yaml`
* Default cleanly from `defaults.yaml`
* Respect the separation of **intent** (YAML) and **execution** (Python)
* Ensure runtime tracking reflects org and network IDs
* Avoid hardcoded identifiers; rely on `runtime.json` if needed

---

> 🧭 This file should guide any user wanting to extend the automation system with a new network feature.

---

*Revision: v1 — 2025-05-07*
