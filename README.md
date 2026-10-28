# Disk Image & Sparsebundle Recovery Tool

A lightweight **macOS utility** written in **Python** that attempts to unlock **macOS disk images** (`*.sparsebundle`, `*.dmg`, `*.sparseimage`) by trying candidate passwords from plain `.txt` wordlist files. This tool is intended for **legitimate data recovery** and **authorised digital forensics** when an image's password has been forgotten.

The tool automates `hdiutil attach` attempts, provides a live progress dashboard, and includes helper commands to avoid attachment and detachment conflicts. Recovery time varies depending on wordlist size, hardware and encryption complexity.

---

## ⚙️ Brief Summary

* Attempts to mount encrypted disk images by feeding candidate passwords to `hdiutil`.
* Supports `.sparsebundle`, `.dmg` and `.sparseimage` disk image formats.
* Automatically discovers images and `.txt` wordlists in the current directory (Mode 1).
* Includes CrackStation's **64 million password Human Only dictionary**.
* Shows a live progress dashboard (checked count, rate, ETA).
* Provides interactive controls (skip wordlist, skip image, quit).
* Allows manual ordering of disk images before recovery begins.
* Includes a recommended `clean` helper to detach mounted devices.

---

## ▶️ Run Script (3 steps)

### 1) Add your files

Clone the repository using Git LFS to retrieve the included password dictionary:

```bash
git lfs install
git clone https://github.com/Praetorian301/MacOS-DiskImage-Recovery-Tool.git
```

Navigate to the script directory:

```bash
cd MacOS-DiskImage-Recovery-Tool/DiskImageCrackerMacOS
```

* Place disk images in the same folder as `cracker.py` (for example: `test.sparsebundle`, `test.dmg`).
* Place one or more plain `.txt` wordlists in the same folder (Mode 1 automatically discovers them).
* The included `human.txt` contains approximately 64 million passwords from CrackStation.
* Additional dictionaries can be downloaded from CrackStation, SecLists and Weakpass. **Only use wordlists you are authorised to use.**

**Requirements:** macOS, Python 3 and the `rich` Python package.

Install the required dependency:

```bash
python3 -m pip install rich
```

### 2) Make the `clean` helper available (recommended)

The `clean` helper detaches mounted disk devices to avoid attachment and detachment conflicts.

* Temporary alias (paste the command into macOS Terminal):

```bash
alias clean="hdiutil info | grep '/dev/disk' | awk '{print \$1}' | xargs -n1 sudo hdiutil detach -force"
```

* Dry run (see devices that would be detached):

```bash
hdiutil info | grep '/dev/disk' | awk '{print $1}'
```

**Warning:** The `clean` command may forcibly detach unrelated mounted volumes. Check the listed devices before running it.

### 3) Run from the script directory

From the `DiskImageCrackerMacOS` folder:

```bash
chmod +x ./cracker.py
# Optional: run 'clean' after checking mounted devices
clean
python3 cracker.py
```

Press **Enter** to select Mode 1 (Local Wordlists), then follow the prompts to begin password recovery.

**Keyboard controls:**

* `s` + Enter, skip the current wordlist.
* `b` + Enter, skip the current disk image.
* `q` + Enter, quit the recovery session.

---

## 🔎 Process Overview

* Automatically scans the current directory for supported disk images and `*.txt` wordlists.
* Allows users to select the processing order of detected disk images.
* Attempts to attach each encrypted image using `hdiutil`, supplying candidate passwords through standard input.
* Monitors the `hdiutil` process, with an exit code of `0` indicating a successful attachment.
* Displays a live dashboard with password attempts, checking speed, elapsed time and ETA.
* Supports skipping wordlists, skipping images or terminating the session.
* On successful recovery, displays the recovered password and attempts to detach the mounted image.

---

## ⚠️ Troubleshooting

* **No supported disk images found:** Verify that `.sparsebundle`, `.dmg` or `.sparseimage` files are in the same folder as `cracker.py`.
* **No wordlists detected:** Ensure your password dictionaries use the `.txt` extension and are in the current directory.
* **`full.lst` not detected:** Rename the dictionary to `full.txt`, as the current script only recognises `.txt` files.
* **Missing `rich` module:** Run `python3 -m pip install rich`.
* **Git LFS dictionary missing:** Run `git lfs pull` from the repository root.
* **`clean` prints nothing:** No matching mounted disk devices were found.
* **Device won't detach:** Check which process is using the disk image, then manually detach the appropriate device using `hdiutil detach /dev/diskN`.
* **Long recovery times:** Large dictionaries may take considerable time to process. Try smaller, more targeted wordlists first.
* **`hdiutil` unavailable:** The utility requires macOS and cannot run natively on Windows.

---

## 📂 Folder Layout

```text
MacOS-DiskImage-Recovery-Tool/
│
├── .gitattributes
├── .gitignore
├── README.md
│
└── DiskImageCrackerMacOS/
    ├── cracker.py
    ├── Instructions.txt
    │
    ├── human.txt
    ├── full.lst              (Optional, local only)
    │
    ├── test.dmg
    ├── test.txt
    ├── testTwo.txt
    │
    └── test.sparsebundle/
        ├── Info.bckup
        ├── Info.plist
        ├── lock
        └── token
```

> Note: The `human.txt` dictionary is included through Git LFS. The larger `full.lst` dictionary must be downloaded separately and renamed to `full.txt` for use with the current script. Your project may use slightly different filenames.

---

## 📚 Wordlists

The repository includes CrackStation's **Human Passwords Only** dictionary (`human.txt`), containing approximately 64 million real passwords collected from historical website database breaches.

The full CrackStation dictionary (`full.lst`) contains approximately 1.49 billion entries sourced from password leaks, dictionaries, Wikipedia and other public text collections. It is available separately due to its large file size.

| Dictionary | Entries | Uncompressed Size | Availability |
|---|---|---|---|
| `human.txt` | ~64 million | 684 MiB | Included via Git LFS |
| `full.lst` | ~1.49 billion | 15 GiB | Download separately |

**Recommended public wordlist sources:**

* [CrackStation](https://crackstation.net/crackstation-wordlist-password-cracking-dictionary.htm), Human Only dictionary included.
* [SecLists (GitHub)](https://github.com/danielmiessler/SecLists)
* [Weakpass](https://weakpass.com/)

**Note:** The script currently detects `.txt` files only. Rename `full.lst` to `full.txt` before using it.

CrackStation dictionaries are licensed under [Creative Commons Attribution ShareAlike 3.0](https://creativecommons.org/licenses/by-sa/3.0/).

Only use wordlists on disk images you own or have explicit permission to examine.

---

## ⚖️ Warnings & Legal

* **Authorised use only.** Run this tool only on disk images you own or have explicit permission to test.
* The `clean` helper and script's cleanup operations may forcibly detach mounted volumes. Use with caution.
* **Unauthorised access to systems or data is illegal.** Misuse of this utility may constitute a criminal offence.
* If sensitive credentials or data are exposed during recovery, handle them securely.

---

## 🧾 Notes & Limitations

* Recovery success depends on whether the correct password is present in the selected dictionaries.
* Large wordlists may require substantial processing time.
* Performance depends on hardware resources, encryption configuration and disk image type.
* The tool automates `hdiutil` attachments rather than using GPU acceleration.
* Only `.txt` dictionaries are automatically detected by the current script.
* The utility requires macOS and does not run natively on Windows or Linux.

---

## 👨‍💻 Credits & Contact

Created by **[@Praetorian301](https://github.com/Praetorian301)**.

Password dictionaries provided by [CrackStation](https://crackstation.net/), licensed under Creative Commons Attribution ShareAlike 3.0.

**Repository:** [MacOS Disk Image Recovery Tool](https://github.com/Praetorian301/MacOS-DiskImage-Recovery-Tool)

---
