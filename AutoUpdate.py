import os
import shutil
import threading
import tkinter as tk
from tkinter import messagebox
import requests
import json
import datetime
import re
import argparse
import sys
import subprocess

# ------------------------------
# Helper functions for version handling
# ------------------------------
def parse_version(ver_str):
    """
    Extracts version components from a version string.
    Expected format (with optional app name): "MJ-Control v{major}.{minor}[-{release_type}{number}]"
    Example: "MJ-Control v0.2-pre1" or "MJ-Control v1.0"
    Returns a tuple: (major, minor, release_type, release_number)
    """
    ver_str = ver_str.strip()
    m = re.search(r'v(\d+)\.(\d+)(?:-([a-zA-Z]+)(\d+))?', ver_str)
    if not m:
        raise ValueError("Invalid version format: " + ver_str)
    major = int(m.group(1))
    minor = int(m.group(2))
    release_type = m.group(3) if m.group(3) else "stable"
    release_num = int(m.group(4)) if m.group(4) else 0
    return (major, minor, release_type.lower(), release_num)

def compare_versions(v1, v2):
    """
    Compares two version strings.
    Returns positive if v1 > v2, zero if equal, negative if v1 < v2.
    Ordering: pre < beta < rc < stable.
    """
    order = {"pre": 1, "beta": 2, "rc": 3, "stable": 4}
    t1 = parse_version(v1)
    t2 = parse_version(v2)
    if t1[0] != t2[0]:
        return t1[0] - t2[0]
    if t1[1] != t2[1]:
        return t1[1] - t2[1]
    rt1 = order.get(t1[2], 0)
    rt2 = order.get(t2[2], 0)
    if rt1 != rt2:
        return rt1 - rt2
    return t1[3] - t2[3]

# ------------------------------
# Functions to load and save version info (JSON-based)
# ------------------------------
def load_version(version_path):
    if not os.path.exists(version_path):
        return {"version": "v0", "installed_on": "", "previous_version": ""}
    with open(version_path, "r") as f:
        return json.load(f)

def save_version(version_path, new_version, current_version):
    version_data = {
        "version": new_version,
        "installed_on": datetime.datetime.now().isoformat(),
        "previous_version": current_version
    }
    with open(version_path, "w") as f:
        json.dump(version_data, f, indent=2)

# ------------------------------
# Function to load configuration from a JSON file
# ------------------------------
def load_config(config_path="updater_config.json"):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file '{config_path}' not found.")
    with open(config_path, "r") as f:
        return json.load(f)

# ------------------------------
# Placeholder functions for CLI process management
# ------------------------------
def stop_running_instance():
    # Implement your logic to stop the running instance here.
    print("Simulating: Stopping running instance...")

def relaunch_executable(exe_path):
    # Relaunch the new version.
    print("Simulating: Relaunching the new version...")
    try:
        if sys.platform.startswith("win"):
            os.startfile(exe_path)
        else:
            subprocess.Popen(["chmod", "+x", exe_path])
            subprocess.Popen([exe_path])
    except Exception as e:
        print("Error relaunching executable:", e)

# ------------------------------
# Main update process (used by both GUI and CLI)
# ------------------------------
def perform_update_process(config, log_func=print):
    version_file = config.get("version_file", "version.json")
    backup_dir = config.get("backup_dir", ".backup")
    
    # Load current version info
    local_version_data = load_version(version_file)
    current_version = local_version_data.get("version", "v0")
    log_func("Current version: " + current_version)
    
    # Fetch manifest
    manifest_url = config.get("manifest_url")
    if not manifest_url:
        log_func("Manifest URL not specified in configuration.")
        return False
    response = requests.get(manifest_url)
    if response.status_code != 200:
        log_func("Failed to fetch manifest. Status: " + str(response.status_code))
        return False
    manifest = response.json()
    remote_version = manifest.get("version", "v0").strip()
    log_func("Remote version: " + remote_version)

    # Compare versions
    if compare_versions(remote_version, current_version) <= 0:
        log_func("No update available.")
        return False

    log_func("Update available!")
    # Prompt the user (CLI mode uses input, GUI mode uses messagebox)
    if log_func == print:
        answer = input("Update to version {}? [y/N]: ".format(remote_version)).strip().lower() == 'y'
    else:
        answer = messagebox.askyesno("Update Available", f"Update to version {remote_version}?")
    if not answer:
        log_func("User cancelled update.")
        return False

    # Create backup folder
    log_func("Creating backup…")
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)
    os.makedirs(backup_dir)
    
    # Backup files from the manifest.
    for file_info in manifest.get("files", []):
        raw_path = file_info.get("name")
        if not raw_path:
            continue
        # Determine the local file to backup.
        if file_info.get("name", "").endswith(".exe"):
            # For executables, if no "previous_name" is provided, use local version string.
            previous_name = file_info.get("previous_name")
            if previous_name:
                backup_source = previous_name.lstrip("/")
            else:
                backup_source = f"{current_version}.exe"
        else:
            backup_source = file_info.get("name", "").lstrip("/")
        if os.path.exists(backup_source):
            backup_path = os.path.join(backup_dir, backup_source)
            os.makedirs(os.path.dirname(backup_path) or ".", exist_ok=True)
            # For executables, move (i.e. delete the original) instead of copying.
            if backup_source.lower().endswith(".exe"):
                shutil.move(backup_source, backup_path)
                log_func(f"Moved (backed up) {backup_source} to {backup_path}")
            else:
                shutil.copy2(backup_source, backup_path)
                log_func(f"Copied {backup_source} to {backup_path}")
    
    # Also backup the version file.
    if os.path.exists(version_file):
        backup_vfile = os.path.join(backup_dir, version_file)
        os.makedirs(os.path.dirname(backup_vfile) or ".", exist_ok=True)
        shutil.copy2(version_file, backup_vfile)
        log_func(f"Backed up {version_file} to {backup_vfile}")
    
    log_func("Downloading new files…")
    # Download new files.
    for file_info in manifest.get("files", []):
        raw_path = file_info.get("name")
        download_url = file_info.get("download_url")
        if not raw_path or not download_url:
            continue
        # Save new file using the manifest's "name".
        target_path = raw_path.lstrip("/")
        log_func(f"Updating {target_path} …")
        r = requests.get(download_url, stream=True)
        if r.status_code == 200:
            os.makedirs(os.path.dirname(target_path) or ".", exist_ok=True)
            with open(target_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            log_func(f"Updated {target_path}")
        else:
            raise Exception(f"Download failed for {target_path}. Status code: {r.status_code}")
    
    # Update version file
    new_version = manifest.get("version", "v0")
    save_version(version_file, new_version, current_version)
    log_func("Update successful to version " + new_version)
    return True

# ------------------------------
# GUI Application
# ------------------------------
class UpdaterApp:
    def __init__(self, master, config):
        self.master = master
        self.config = config
        master.title("Auto Updater")

        self.log_text = tk.Text(master, state='disabled', width=80, height=20)
        self.log_text.pack(padx=10, pady=10)

        self.update_button = tk.Button(master, text="Check for Updates", command=self.start_update)
        self.update_button.pack(pady=(0, 10))

    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def start_update(self):
        t = threading.Thread(target=self.check_update)
        t.daemon = True
        t.start()

    def check_update(self):
        try:
            self.log("Checking for update…")
            updated = perform_update_process(self.config, log_func=self.log)
            if updated:
                self.log("Restarting application…")
                self.master.after(2000, lambda: self.master.quit())
            else:
                self.log("Update check complete.")
        except Exception as e:
            self.log("Error during update check: " + str(e))

# ------------------------------
# CLI Mode Update Process
# ------------------------------
def cli_update(config):
    print("Checking for update…")
    try:
        updated = perform_update_process(config, log_func=print)
        if updated:
            print("Update applied successfully.")
            stop_running_instance()
            # Assume main executable is the first file in the manifest.
            manifest = requests.get(config.get("manifest_url")).json()
            main_file = manifest.get("files", [])[0]
            target_exe = main_file.get("name", "").lstrip("/")
            if target_exe:
                relaunch_executable(target_exe)
        else:
            print("No update applied.")
    except Exception as e:
        print("Error during CLI update: " + str(e))

# ------------------------------
# Main entry point
# ------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto Updater")
    parser.add_argument("--cli-update", action="store_true", help="Run update in CLI mode without GUI")
    args = parser.parse_args()

    try:
        config = load_config("updater_config.json")
    except Exception as e:
        print("Error loading configuration: " + str(e))
        sys.exit(1)

    if args.cli_update:
        cli_update(config)
    else:
        root = tk.Tk()
        app = UpdaterApp(root, config)
        root.mainloop()
