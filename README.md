# Disk Image & Sparsebundle Recovery Tool

A lightweight macOS utility written in **Python** that attempts to unlock macOS disk images (`*.sparsebundle`, `*.dmg`, `*.sparseimage`) by trying candidate passwords from plain `.txt` wordlist files. This tool is intended for **legitimate data recovery** and **authorized digital-forensics** work when an image’s password has been forgotten.

The tool automates `hdiutil attach` attempts, provides a live progress dashboard, and includes helper commands to avoid attach/detach conflicts. Recovery time varies with wordlist size and hardware — small lists can finish in a few hours, while large lists may take much longer.

---

## ⚙️ Brief Summary

* Attempts to mount encrypted disk images by feeding candidate passwords to `hdiutil`.
* Auto-discovers images and `.txt` wordlists in the repository root (Mode 1).
* Shows a live progress dashboard (checked count, rate, ETA).
* Provides interactive controls (skip file, skip image, quit).
* Includes a recommended `clean` helper to safely detach mounted devices.

---

## ▶️ Run Script (3 steps)

### 1) Add your files

* Place disk images in the repo root (for example: `test.sparsebundle`, `test.dmg`).
* Place one or more plain `.txt` wordlists in the same folder (Mode 1 auto-discovers them).
* Use public, legal wordlists (e.g., SecLists, Weakpass) — **only use lists you are allowed to use**.

### 2) Make the `clean` helper available (recommended)

A `clean` helper detaches mounted disks to avoid attach/detach conflicts.

* Temporary alias (paste the command in Terminal):

```bash
alias clean="hdiutil info | grep '/dev/disk' | awk '{print \$1}' | xargs -n1 sudo hdiutil detach -force"
```

* Dry run (see devices that would be detached):

```bash
hdiutil info | grep '/dev/disk' | awk '{print $1}'
```

### 3) Run from the repository root

```bash
chmod +x ./cracker.py
# Optional: run 'clean' to detach existing devices first
clean
python3 cracker.py
```

---

## 🔎 Process Overview

* Auto-scans the repository folder for supported disk images and `*.txt` wordlists.
* For each image it attempts to attach using `hdiutil`, sending candidate passwords via stdin.
* Monitors the `hdiutil` process; an exit code of `0` indicates a successful attach (password found).
* Shows a live progress dashboard with counts, rate, and ETA.
* Accepts simple keyboard commands to control the run:

  * `s` + Enter → skip current wordlist (file)
  * `b` + Enter → skip current image/bundle
  * `q` + Enter → quit the run
* On success or exit the script attempts to detach mounted volumes and performs a cleanup sweep.

---

## 🧠 Script Logic (detailed)

1. **Discovery** — find disk images in the repo root and `*.txt` wordlists (Mode 1).
2. **Order** — present an order of images (automatic or manual reorder supported).
3. **For each image**:

   * Iterate wordlists line-by-line and try each password.
   * Use `hdiutil attach <image> -stdinpass` to provide the password programmatically.
   * Monitor `hdiutil` exit code: `0` → success, non-zero → continue.
4. **Interrupts & controls**:

   * `s` to skip current wordlist file.
   * `b` to skip current image.
   * `q` to quit.
5. **Cleanup** — attempts to detach any mounted volumes and performs a detach sweep on exit.

---

## ⚠️ Troubleshooting

* **“No `.sparsebundle` files found”** — verify images are in the repository root and correctly named.
* **`clean` prints nothing** — there are no mounted `/dev/disk` entries to detach.
* **Device won’t detach** — check for processes using the device or reboot the machine.
* **`hdiutil` behaves differently for some image types** — test `hdiutil` manually to confirm behavior.
* If `hdiutil` prompts for GUI interaction, ensure you’re running from a Terminal with appropriate permissions.

---

## 📂 Folder Layout

```
MacOS-DiskImage-Recovery-Tool/
│
├── .gitattributes
├── README.md
│
└── DiskImageCrackerMacOS/
    ├── cracker.py
    ├── Instructions.txt
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

> Note: Your project may use slightly different filenames — adjust the layout above accordingly.

---

## ⚖️ Warnings & Legal

* **Authorized use only.** Run this tool only on disk images you own or for which you have explicit permission to test.
* `clean` uses `sudo` and forcibly detaches volumes — use with caution.
* **Unauthorized access to systems or data is illegal.** Misuse of this tool may constitute a criminal offense.
* If you accidentally expose credentials or sensitive data, revoke them immediately and follow your security policy.

---

## 📚 Wordlists

Recommended public sources for legal wordlists:

* [SecLists (GitHub)](https://github.com/danielmiessler/SecLists)
* [Weakpass](https://weakpass.com)

Only use lists you have legal permission to run against the target images.

---

## 🧾 Notes & Limitations

* Success depends on wordlist quality and size. Large lists can take a very long time.
* Rate and performance depend on machine resources and image type.
* The tool automates `hdiutil` attachments — if an image uses non-standard encryption or key derivation, it may not be crackable by simple brute force.

---

## 👨‍💻 Credits & Contact

Created by **[@Praetorian301](https://github.com/Praetorian301)**.
If you find bugs or want to contribute, open an issue or a pull request.

---
