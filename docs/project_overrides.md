

# 🔧 Per-Network Project-Level Overrides

This document explains how to apply custom configuration on a per-network basis within a project. This is essential for tailoring deployments in environments with distinct hub/spoke roles or differing connectivity requirements.

---

## 🧠 Overview

Each network defined in a project (within `config/manifest.yaml`) can specify its own overrides for key network constructs like firewall rules, wireless SSIDs, ports, and routes. These overrides are resolved at runtime during deployment and override the default `common/` values.

---

## 📂 File Structure

Your typical config layout should look like:

```
config/
├── common/
│   └── firewall/
│       └── mx_firewall.yaml
└── projects/
    └── percy_street/
        └── firewall/
            └── mx_firewall.yaml
```

---

## 🧾 Manifest Example

```yaml
projects:
  - name: Percy Street
    slug: percy_street
    networks:
      - base_name: Studio Hub
        slug: studio_hub
        config:
          firewall: projects/percy_street/firewall/mx_firewall.yaml

      - base_name: Studio Spoke
        slug: studio_spoke
        config:
          firewall: projects/percy_street/firewall/mx_firewall_spoke.yaml
```

Each `network.config.firewall` value must point to a relative YAML path inside `config/`.

---

## 🔄 Runtime Behavior

### What Happens

- If a `network.config.<key>` is present, the system will load that YAML instead of the `common/` version.
- The override is merged into the final config using the `assemble_full_config()` pattern.
- If the override path is invalid or missing, it silently falls back to the common config.

---

## 🧪 Testing Per-Network Firewall Rules

1. Create distinct override files for each network.
2. Add paths under the appropriate network in `manifest.yaml`.
3. Run a deployment and verify that the correct rules appear in the summary log.

---

## 🔁 Supported Constructs (as of now)

| Construct        | Manifest Key | Override Supported |
|------------------|--------------|---------------------|
| Firewall Rules   | `firewall`   | ✅ Yes              |
| Wireless SSIDs   | `wireless`   | 🔜 Soon             |
| MX Ports         | `mx_ports`   | 🔜 Soon             |
| Static Routes    | `static_routes` | 🔜 Soon          |

---

## 📌 Summary

This pattern provides:
- Fine-grained control at the network level
- Clean separation of shared vs custom config
- Scalable override support for future features

Use it wherever network roles diverge in purpose or security policy.