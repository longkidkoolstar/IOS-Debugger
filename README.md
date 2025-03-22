Here's the corrected and final version of your `README.md` with proper formatting, fixed code blocks, and your local screenshot path updated to a GitHub-friendly relative path (`screenshots/ui.png`). Just copy and paste this into your `README.md` file on GitHub:

---

### ✅ Final `README.md`

```markdown
# 🧭 iOS Safari Remote Debugger GUI

A simple graphical interface built with Python and Tkinter to help developers debug Safari on iOS devices using Apple's WebKit Remote Debugging Protocol.

This tool allows you to:
- Start and stop the local WebKit remote debugging server
- View a list of inspectable pages on connected iOS Safari instances
- Open the Safari DevTools for a selected page directly in your browser

---

## 📦 Features

- ✅ Save and remember WebKit folder path
- ✅ Start/stop WebKit remote debugging server with a click
- ✅ List all currently available inspectable Safari tabs
- ✅ Open Safari's DevTools UI for selected pages
- ✅ Console log output built-in
- ✅ Cross-platform support (Windows, macOS, Linux)

---

## 🚀 Getting Started

### 🔧 Requirements

- Python 3.7+
- Pip packages: `requests`, `beautifulsoup4`

You can install the requirements using:

```bash
pip install requests beautifulsoup4
```

---

## 🛠️ Setup

1. Clone this repository:

```bash
git clone https://github.com/longkidkoolstar/ios-safari-debugger-gui.git
cd ios-safari-debugger-gui
```

2. Run the GUI:

```bash
python main.py
```

3. Select your local **WebKit folder** (containing `start.sh` or `start.ps1`) via the "Browse" button.

> ⚠️ Make sure your iOS device is connected and Safari is open with Web Inspector enabled.

---

## 🧪 Usage

- Click `Start Debugging Server` to launch the local server.
- Click `Refresh Pages` to load currently opened tabs on your iOS device.
- Select any page from the list and click `Open Debugger` to open Safari DevTools in your browser.
- Double-clicking a page also opens it directly.

---

## 📁 Folder Structure

```
.
├── main.py                   # The main application file
├── README.md                 # This file
├── screenshots/
│   └── ui.png                # Screenshot of the GUI
└── .ios_safari_debugger.ini  # Auto-generated config file (saves WebKit path)
```

---

## 📸 Screenshots

![Main UI](screenshots/ui.png)

---

## 💡 Notes

- This tool does **not** include WebKit itself. You need to [build WebKit from source](https://webkit.org) or use a precompiled version with `start.sh` or `start.ps1`.
- Make sure port `9221` is available and not blocked by firewalls.

---

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for more info.

---

## 🙏 Credits

Built by [longkidkoolstar](https://github.com/longkidkoolstar). Inspired by Apple's WebKit DevTools and the desire for a simple UI to debug iOS Safari.
```

---

