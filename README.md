# 🔁 Reverse SSH Tunnel - Python Utility

A lightweight Python utility to automate the setup of a **reverse SSH tunnel**, allowing you to expose a local service (**SSH**) to a remote server (**Linux** kernel) – even behind NAT or a firewall.

---

## 📚 Table of Contents

* [Overview](#-overview)
* [Features](#-features)
* [Installation](#-installation)
* [Usage](#-usage)
* [Options](#-options)
* [How It Works](#-how-it-works)
* [Stopping the Tunnel](#-stopping-the-tunnel)
* [Security Considerations](#-security-considerations)
* [Requirements](#-requirements)
* [Troubleshooting](#-troubleshooting)
* [Contributing](#-contributing)
* [License](#-license)

---

## 📌 Overview

This tool creates a **reverse SSH tunnel** from a local machine (e.g. laptop, Raspberry Pi, VM) to a remote SSH server, exposing a local port (e.g. SSH, HTTP, custom service) through the remote server's public IP.

It’s useful for:

* Accessing systems behind NAT or firewall
* IoT devices
* Remote debugging
* Secure remote access

---

## ✨ Features

* ✅ Auto-generates SSH key pair (RSA 4096 bits)
* ✅ Checks and installs OpenSSH server (on supported systems)
* ✅ Fingerprint integrity validation (`ssh-keygen -l`)
* ✅ Automatically authorizes SSH key on remote
* ✅ Sets up reverse tunnel via `ssh -fNR`
* ✅ Informative logs with status indicators
* ✅ Safe exception handling
* ✅ Works on Linux systems (for the moment)

---

## 🔧 Installation

```bash
git clone https://github.com/baldeuniversel/reverse-ssh.git
cd reverse-ssh-python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🚀 Usage

```bash
python main.py --host <REMOTE_HOST> --user <REMOTE_USER> \
    --remote-port <REMOTE_SSH_PORT> --bind-port <REMOTE_BIND_PORT> \
    --local-port <LOCAL_PORT>
```

### Example

```bash
python main.py --host 128.64.32.8 --user universe \
    --remote-port 1248 --bind-port 8421 --local-port 1632
```

This opens port `1632` (SSH) of the **local machine**, accessible from port `8421` of the **remote machine**.

---

## 🔗 Options

| Option                  | Description                                           |
| ----------------------- | ----------------------------------------------------- |
| `--host \| -h`          | IP or hostname of the remote SSH server               |
| `--user \| -u`          | Username on the remote server                         |
| `--remote-port \| -rp`  | SSH port on the remote server (default: 1248)         |
| `--bind-port \| -bp`    | Port to expose on the remote server (default: 8421)   |
| `--local-port \| -lp`   | Port to expose from the local machine (default : 1632)|
| `--list-tunnel \| -lt`  | List active reverse SSH tunnels                       |
| `--kill-tunnel \| kt`   | Kill a reverse SSH tunnel by bind port (nargs)        |
| `--help`                | To see help                                           |

---

## 🔄 How It Works

1. Checks SSH server and service on local machine
2. Verifies or generates RSA key pair
3. Validates fingerprint for integrity
4. Uploads public key to remote `~/.ssh/authorized_keys`
5. Launches background SSH tunnel using `ssh -fNR`
...

---

## 🚫 Stopping the Tunnel

Find and kill the SSH process manually:

```bash
ps aux | grep "ssh -fN"
kill <PID>
```

Or via the program (e.g):
```
python main.py --kill-tunnel 8421
```

---

## 🔐 Security Considerations

* 🔑 Keys are stored in `~/.ssh/id_rsa` and `id_rsa.pub`
* 🔍 Key fingerprint is verified for consistency
* 🚫 Password login is not used (only key-based auth)
* ✅ Authorized keys are appended safely


---

## ✅ Requirements

* Linux-based system with `apt`
* Python 3.7+
* `openssh-server` (installed automatically if missing)
* Remote SSH server (**Linux kernel**) with access via key-based login or not

---

## 🔩 Troubleshooting

* ❌ *“Bad remote forwarding specification”* → Check port args in your `ssh` command
* ❌ *“Permission denied”* → Ensure public key is authorized correctly on remote
* ✅ Use `sudo ss -tulnp | grep <bind-port>` on remote to verify tunnel

---

## 🤝 Contributing

Feel free to open issues or submit pull requests!

```bash
git checkout -b feature/my-feature
git commit -m "Add my feature"
git push origin feature/my-feature
```

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](https://opensource.org/license/mit) for details.

---

© 2025 – Maintained by \[ Baldé Amadou \]
