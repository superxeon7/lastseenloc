# LastSeenLoc


---

## ⚠️ Important Notice

DO NOT use this project for illegal, unethical, or unauthorized activities.
This repository is intended only for educational purposes, authorized security testing, and research in controlled environments. The author and contributors are not responsible for misuse.

If you are unsure whether your use case is legal, stop and seek legal advice.

---

## 🧭 Description

**LastSeenLoc** iis an educational Python tool that demonstrates how system and network metadata — including simulated geolocation-like metadata — can be collected and analyzed in authorized lab environments.
This project is intended to help students and researchers learn defensive and investigative techniques in cybersecurity, using only simulated or consented data.
> This tool does not perform unauthorized tracking, surveillance, or data collection of real individuals.

---

## ✅ Supported Platforms

This tool is designed to **run on almost all major platforms**, as long as dependencies are properly installed:

* **Linux:** Debian / Ubuntu / Kali, Arch / Manjaro, Fedora, Alpine, etc.
* **macOS:** via Homebrew
* **Windows:** via WSL (Windows Subsystem for Linux) or native Python
* **Android:** via Termux

> 💡 Tip: On Windows, it's recommended to use **WSL** for best compatibility.

---

## 🧰 Requirements

* Internet connection (if the tool fetches external data)
* Proper execution permissions (especially for shell scripts)

---

## ⚙️ Installation

1. **Clone the repository**

```bash
git clone https://github.com/superxeon7/lastseenloc.git
cd lastseenloc
```

2. **Grant permission to the install script**

```bash
chmod +x install.sh
```

3. **Run the installation script**

```bash
./install.sh
```

4. **Run the tool**

```bash
python3 lastseenloc.py
```

5. **Follow on-screen instructions**

---

## 💡 Usage Tips

* **Windows + WSL:** Open WSL terminal and run the same commands above.
* **Termux:** Run `pkg update && pkg install python -y` before running the install script.
* If `python3` is not found, try using `python` instead.

---

## 📱 Example — Running on Termux

```bash
pkg update -y
pkg install python -y
git clone https://github.com/superxeon7/lastseenloc.git
cd lastseenloc
chmod +x install.sh
./install.sh
python3 lastseenloc.py
```

---

## 🤝 Contributing & Support

Want to improve or expand this tool? Feel free to **open an issue** or **submit a pull request** on the repository. For troubleshooting, please include:

* Your operating system
* Python version
* Any error logs or stack traces


