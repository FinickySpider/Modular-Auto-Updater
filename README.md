# Modular-Auto-Updater

Modular-Auto-Updater is a flexible, cross-platform Python tool designed to automate the update process for any application. It uses a modular configuration approach—leveraging external JSON files for configuration, version tracking, and update manifests—so you can easily adapt it for different projects. The tool supports both a GUI mode (built with Tkinter) and a CLI mode for headless environments.

## Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
  - [updater_config.json](#updater_configjson)
  - [updater_manifest.json](#updater_manifestjson)
  - [version.json](#versionjson)
- [Usage](#usage)
  - [GUI Mode](#gui-mode)
  - [CLI Mode](#cli-mode)
- [Versioning](#versioning)
- [Customization and Extensions](#customization-and-extensions)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Modular Configuration:** All settings (file paths, manifest URL, etc.) are managed via an external JSON config file.
- **Multi-file Updates:** Supports updating multiple files in a single operation.
  - Automatically backs up current files before replacing them.
  - Creates necessary directories (including subdirectories) if they do not exist.
  - Moves executable files (deleting the old version) and copies other file types.
- **Version Management:** Uses a JSON-based version file to track the current version, installation time, and previous version.
- **Flexible Version Comparison:** Designed to work with a versioning convention like  
  `ExampleApp v{major}.{minor}-{release-type}{number}`  
  (e.g. `ExampleApp v1.0-beta1`, `ExampleApp v1.0-rc1`, etc.) and compare versions accordingly.
- **GUI and CLI Modes:**  
  - A Tkinter-based GUI provides a read-only log and a “Check for Updates” button.
  - A CLI mode (`--cli-update`) is available for automated updates without launching the UI.
- **Process Management (Placeholders):** Supports stopping a running instance and relaunching the updated executable (customize these placeholders for your environment).

## Architecture Overview

The updater is divided into several modular components:
- **Configuration Module:** Reads settings from `updater_config.json`.
- **Version Management:** Loads and saves version information using `version.json`.
- **Manifest Processing:** Downloads and parses the update manifest (`updater_manifest.json`), which lists the files to update and the new version.
- **Backup and Update Engine:**  
  - Backs up the current files (and moves executables based on the current version from `version.json`).
  - Downloads new files as specified in the manifest.
  - Updates the local version file.
- **User Interface:** Provides both a GUI (with Tkinter) and CLI mode.

## Prerequisites

- Python 3.6+
- Required Python packages: `requests`
- Tkinter (usually comes bundled with Python on Windows and most Linux distributions)

## Installation

Clone the repository:

```bash
git clone https://github.com/FinickySpider/Modular-Auto-Updater.git
cd Modular-Auto-Updater
```

Install dependencies (if not already installed):

```bash
pip install requests
```

## Configuration

All configuration for the updater is stored in external JSON files.

### updater_config.json

This file sets global parameters such as the path for the version file, backup directory, and the URL for the update manifest.

Example:

```json
{
  "version_file": "version.json",
  "backup_dir": ".backup",
  "manifest_url": "https://example.com/ExampleApp/updater_manifest.json"
}
```

### updater_manifest.json

This is the remote manifest that defines the new update. It includes the new version number and a list of files to update.

Example:

```json
{
  "version": "ExampleApp v1.0-beta1",
  "files": [
    {
      "name": "ExampleApp v1.0-beta1.exe",
      "download_url": "https://example.com/ExampleApp/releases/download/v1.0-beta1/ExampleApp.v1.0-beta1.exe"
    },
    {
      "name": "/assets/click.mp3",
      "download_url": "https://example.com/ExampleApp/releases/download/v1.0-beta1/click.mp3"
    }
  ]
}
```

### version.json

This file tracks the currently installed version. It includes the current version string, the installation timestamp, and the previous version.

Example:

```json
{
  "version": "ExampleApp v0.9-alpha2",
  "installed_on": "2025-02-22T16:39:57.169384",
  "previous_version": "ExampleApp v0.9-alpha1"
}
```

**Note:**  
For executable files, if no override is provided in the manifest, the updater will use the local version from `version.json` (e.g. `"ExampleApp v0.9-alpha2"`) and append `.exe` to determine the file to back up.

## Usage

### GUI Mode

To run the updater with a GUI:

```bash
python updater.py
```

This launches a Tkinter window with a read-only log and a "Check for Updates" button. When an update is available, it will prompt you for confirmation and process the update in a separate thread.

### CLI Mode

To run the updater in CLI mode (for automatic updates without the UI), use the `--cli-update` parameter:

```bash
python updater.py --cli-update
```

In CLI mode, the tool prints log messages to the console, prompts you for confirmation, attempts to stop any running instance of the application, performs the update, and then relaunches the updated executable automatically.

## Versioning

This tool is designed to work with a version naming convention:

```
ExampleApp v{major}.{minor}-{release-type}{number}
```

For example:
- `ExampleApp v0.9-alpha1` → First alpha release
- `ExampleApp v0.9-alpha2` → Second alpha release
- `ExampleApp v1.0-beta1` → Beta release before stable
- `ExampleApp v1.0` → First stable release

The updater uses a custom parser and comparator to decide if an update is available based on this convention.

## Customization and Extensions

You can extend Modular-Auto-Updater with additional features:
- **Checksum Verification:** Add an optional field in the manifest for file hashes to verify integrity after download.
- **Post-Update Scripts:** Specify commands or scripts to run after a successful update.
- **Advanced Process Management:** Customize the functions for stopping a running instance and relaunching the new executable using modules like `psutil`.
- **Logging Enhancements:** Integrate with more robust logging frameworks if needed.

## Troubleshooting

- **Caching Issues:**  
  If you face caching problems when fetching the manifest, try using a hard refresh or appending a query string to the manifest URL.
- **Directory Issues:**  
  Ensure that file paths in the manifest do not have unintended leading slashes. The updater normalizes these paths as relative.
- **Version Parsing Errors:**  
  Make sure your version strings follow the expected format. Adjust the regular expression in `parse_version()` if necessary.

## Contributing

Contributions are welcome! Please fork this repository and submit a pull request with improvements or bug fixes. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
