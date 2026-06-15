# APP-Killer_v9000
Just close all APPs, that reserve important hardware!

# Performance Booster

A small **Windows utility** written in Python to quickly free up system resources by:

- closing selected non-critical applications,
- attempting to reduce RAM usage,
- stopping selected non-critical services,
- and cleaning **GPU VRAM usage** for selected NVIDIA processes.

It includes a simple **Tkinter GUI** and can also be used from the **command line**.

## Features

- **Close selected apps** from a predefined safe list
- **Clean RAM** by attempting to empty process working sets
- **Stop selected services** from a predefined safe list
- **Clean GPU VRAM** using `nvidia-smi` for NVIDIA GPUs
- **One-click boost** button in the GUI to run everything at once
- **CLI-friendly functions** for scripting or automation

## How it works

The script only targets applications and services defined in two allowlists:

- `SAFE_PROCESSES`
- `SAFE_SERVICES`

This reduces the risk of killing important system processes, but you should still **review and customize these lists** before using the tool on your machine.

## Requirements

- **Windows**
- **Python 3.9+** recommended
- Python packages:
  - `psutil`
- For VRAM cleanup:
  - **NVIDIA GPU**
  - `nvidia-smi` available in PATH
  - NVIDIA drivers properly installed

## Installation

Clone the repository:

```bash
git clone https://github.com/ChrisFle2003/APP-Killer_v9000.git
cd APP-Killer_v9000
```

Install dependencies:

```bash
pip install psutil
```

## Usage

### Run the GUI

Start the script normally:

```bash
python kill_apps_for_ram.py
```

This opens a desktop window with these actions:

- **Programme schließen** – closes allowlisted applications
- **RAM bereinigen** – attempts to reduce RAM usage
- **Unkritische Dienste stoppen** – stops allowlisted services
- **GPU VRAM bereinigen** – kills allowlisted GPU processes using VRAM
- **ALLES BOOSTEN** – runs all cleanup actions

### Use from CLI / another script

You can import the module and call the CLI-safe function:

```python
from kill_apps_for_ram import boost_from_cli

boost_from_cli()
```

Or call individual functions:

```python
from kill_apps_for_ram import kill_programs, clean_ram, stop_safe_services, clean_vram

kill_programs(show_gui=False)
clean_ram(show_gui=False)
stop_safe_services(show_gui=False)
clean_vram(show_gui=False)
```

## Example safe lists

The script includes allowlists such as:

- browsers like `msedge.exe`
- launchers like `steam.exe`, `epicgameslauncher.exe`
- apps like `onedrive.exe`, `copilot.exe`
- services like `steamclientservice`, `wuauserv`, `docker`

You should edit these lists to match your own setup.

## Important notes

### 1. Windows-only behavior

This script uses Windows-specific APIs and commands, including:

- `ctypes.WinDLL("psapi")`
- `sc stop`
- PowerShell commands

It will **not work properly on Linux or macOS**.

### 2. Admin privileges may be required

Some actions may fail silently unless the script is run with **administrator privileges**, especially:

- stopping services,
- accessing some processes,
- cleaning memory for protected processes.

### 3. VRAM cleanup limitations

The VRAM cleanup only works when:

- `nvidia-smi` is installed and available,
- an NVIDIA GPU is present,
- GPU compute processes are visible to `nvidia-smi`.

Also, the script only kills GPU processes whose executable names are included in `SAFE_PROCESSES`.

### 4. Some "safe" items may still matter to you

Even though the script uses an allowlist, it may still close apps or stop services you currently need. Review the defaults carefully before running it.

## Recommended improvements

If you plan to expand this project, here are some useful next steps:

- add logging instead of silently ignoring exceptions,
- add a dry-run mode,
- add a settings/config file for custom process and service lists,
- detect admin rights and warn the user,
- improve localization (the script currently mixes German UI text with English code),
- package it as an `.exe` for easier Windows use.

## Project structure

```text
kill_apps_for_ram.py   # Main script with GUI and CLI functions
```

## Disclaimer

Use this script at your own risk.

Although it is designed to target only allowlisted apps and services, force-killing processes and stopping services can interrupt workflows, cause unsaved data loss, or affect system behavior.

## License

Add your preferred license here, for example:

- MIT License
- Apache 2.0
- GPL-3.0

---

If you publish this on GitHub, replace the repository URL and add your license information.
