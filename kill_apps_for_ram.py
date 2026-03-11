import psutil
import ctypes
import tkinter as tk
from tkinter import messagebox
import subprocess


SAFE_PROCESSES = {
    # Browser
    "msedge.exe", "msedgewebview2.exe",

    # Gaming / Launcher
    "steam.exe", "steamservice.exe", "steamwebhelper.exe",
    "epicgameslauncher.exe", "epicwebhelper.exe",
    "eadesktop.exe", "eabackgroundservice.exe", "eacefsubprocess.exe",
    "xboxpcapp.exe", "xboxpcappft.exe", "xboxpct​ray.exe",

    # Apps
    "claude.exe", "copilot.exe",
    "onedrive.exe",
    "pet.exe", "phoneexperiencehost.exe",

    # Basic tools
    "notepad.exe", "filecoauth.exe", "appactions.exe",
}

SAFE_SERVICES = {
    # Nur nicht-systemkritische Services
    "steamclientservice",
    "wuauserv",   # Windows Update (stoppen ist sicher, Windows startet selbst bei Bedarf)
    "docker",
    "docker desktop service",
    "onedrive",
}


# -------------------------------
# GPU-HILFSFUNKTION
# -------------------------------

def get_vram_usage():
    """
    Liefert (used_mb, total_mb) des ersten NVIDIA-GPUs.
    Gibt (None, None) zurück, wenn nicht abfragbar.
    """
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        line = result.stdout.strip().splitlines()[0]
        used_str, total_str = [x.strip() for x in line.split(",")]
        used = int(used_str)
        total = int(total_str)
        return used, total
    except Exception:
        return None, None


# -------------------------------
# AKTIONEN (GUI & CLI)
# -------------------------------

def kill_programs(show_gui: bool = True) -> int:
    """
    Beendet Prozesse aus SAFE_PROCESSES.
    Gibt die Anzahl der gekillten Prozesse zurück.
    """
    killed = 0
    for proc in psutil.process_iter(["pid", "name"]):
        name = proc.info["name"]
        if name and name.lower() in SAFE_PROCESSES:
            try:
                proc.kill()
                killed += 1
            except Exception:
                pass

    if show_gui:
        messagebox.showinfo("Fertig", f"{killed} Programme wurden beendet.")
    else:
        print(f"[Programme] {killed} Programme wurden beendet.")

    return killed


def try_clear_mmagent():
    ps_cmd = r"""
    if (Get-Command Clear-MMAgentMemoryGarbageCollect -ErrorAction SilentlyContinue) {
        Clear-MMAgentMemoryGarbageCollect
    }
    """
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def clean_ram(show_gui: bool = True) -> None:
    # Working Set leeren (wie gehabt)
    try:
        psapi = ctypes.WinDLL("psapi")
        OpenProcess = ctypes.windll.kernel32.OpenProcess
        EmptyWorkingSet = psapi.EmptyWorkingSet
        PROCESS_SET_QUOTA = 0x0100
        PROCESS_QUERY_INFORMATION = 0x0400

        for proc in psutil.process_iter(['pid']):
            try:
                handle = OpenProcess(
                    PROCESS_SET_QUOTA | PROCESS_QUERY_INFORMATION,
                    False, proc.pid
                )
                if handle:
                    EmptyWorkingSet(handle)
            except Exception:
                pass
    except Exception:
        pass

    # Standby-List versuchen zu leeren, aber nur wenn Cmdlet vorhanden
    try_clear_mmagent()

    if show_gui:
        messagebox.showinfo("RAM", "RAM-Bereinigung abgeschlossen.")
    else:
        print("[RAM] RAM-Bereinigung abgeschlossen.")



def stop_safe_services(show_gui: bool = True) -> int:
    stopped = 0
    for service in SAFE_SERVICES:
        try:
            subprocess.run(["sc", "stop", service], capture_output=True)
            stopped += 1
        except Exception:
            pass

    if show_gui:
        messagebox.showinfo("Dienste", f"{stopped} Dienste wurden gestoppt.")
    else:
        print(f"[Dienste] {stopped} Dienste wurden gestoppt.")

    return stopped


def clean_vram(show_gui: bool = True) -> None:
    """
    Versucht, VRAM freizugeben, indem GPU-Prozesse beendet werden,
    die in SAFE_PROCESSES stehen und laut nvidia-smi VRAM belegen.
    """
    # Vorher-Werte
    before_used, total = get_vram_usage()

    # Prozesse mit GPU-Nutzung abfragen
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-compute-apps=pid,used_memory",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        msg = (
            "Das Tool 'nvidia-smi' wurde nicht gefunden.\n"
            "Bitte stelle sicher, dass ein NVIDIA-Treiber installiert ist."
        )
        if show_gui:
            messagebox.showerror("GPU VRAM", msg)
        else:
            print(f"[GPU VRAM] {msg}")
        return
    except subprocess.CalledProcessError:
        msg = (
            "GPU-Informationen konnten nicht abgefragt werden.\n"
            "Eventuell sind gerade keine Compute-Apps aktiv."
        )
        if show_gui:
            messagebox.showerror("GPU VRAM", msg)
        else:
            print(f"[GPU VRAM] {msg}")
        return

    lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    if not lines:
        if before_used is None:
            msg = "Es wurden keine GPU-Prozesse gefunden."
        else:
            msg = (
                "Es wurden keine GPU-Prozesse gefunden.\n"
                f"Aktueller VRAM: {before_used} MB von {total} MB."
            )
        if show_gui:
            messagebox.showinfo("GPU VRAM", msg)
        else:
            print(f"[GPU VRAM] {msg}")
        return

    killed = 0
    freed_mb = 0

    for line in lines:
        try:
            pid_str, mem_str = [x.strip() for x in line.split(",")]
            pid = int(pid_str)
            used_mem = int(mem_str)  # in MB
        except Exception:
            continue

        try:
            proc = psutil.Process(pid)
            name = proc.name().lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

        # Nur Prozesse killen, die in SAFE_PROCESSES stehen
        if name in SAFE_PROCESSES:
            try:
                proc.kill()
                killed += 1
                freed_mb += used_mem
            except Exception:
                pass

    after_used, _ = get_vram_usage()

    msg_lines: list[str] = []
    msg_lines.append(f"{killed} GPU-Prozess(e) wurden beendet.")
    msg_lines.append(f"Geschätzter freigegebener VRAM: ~{freed_mb} MB.")

    if before_used is not None and after_used is not None and total is not None:
        msg_lines.append(f"VRAM vorher: {before_used} MB von {total} MB.")
        msg_lines.append(f"VRAM nachher: {after_used} MB von {total} MB.")

    if show_gui:
        messagebox.showinfo("GPU VRAM", "\n".join(msg_lines))
    else:
        print("[GPU VRAM]", " | ".join(msg_lines))


def boost_all():
    """
    GUI-Variante: zeigt weiterhin Messageboxen an.
    """
    kill_programs()
    clean_ram()
    stop_safe_services()
    clean_vram()
    messagebox.showinfo("Perfekt!", "Komplettes Boosting (inkl. GPU VRAM) abgeschlossen.")


# -------------------------------
# CLI-BOOST-FUNKTION
# -------------------------------

def boost_from_cli():
    """
    Für anderen Tools & reine CLI-Nutzung.
    Keine GUI-Popups, nur Konsolenausgabe.
    """
    print("Starte CLI-Boost: Programme, RAM, Dienste, GPU VRAM ...")
    killed = kill_programs(show_gui=False)
    clean_ram(show_gui=False)
    stopped = stop_safe_services(show_gui=False)
    clean_vram(show_gui=False)
    print(f"Zusammenfassung: {killed} Programme beendet, {stopped} Dienste gestoppt.")
    print("RAM & VRAM Boosting abgeschlossen.")


# -------------------------------
# GUI STARTEN (nur bei direktem Aufruf)
# -------------------------------

def start_gui():
    root = tk.Tk()
    root.title("Performance Booster")
    root.geometry("320x360")
    root.resizable(False, False)

    tk.Label(root, text="🚀 Performance Booster", font=("Arial", 16)).pack(pady=10)

    tk.Button(root, text="Programme schließen", command=kill_programs, width=25).pack(pady=5)
    tk.Button(root, text="RAM bereinigen", command=clean_ram, width=25).pack(pady=5)
    tk.Button(root, text="Unkritische Dienste stoppen", command=stop_safe_services, width=25).pack(pady=5)
    tk.Button(root, text="GPU VRAM bereinigen", command=clean_vram, width=25).pack(pady=5)
    tk.Button(root, text="🔥 ALLES BOOSTEN", command=boost_all, width=25, bg="red", fg="white").pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    # Wenn du das Script direkt startest: GUI
    start_gui()
