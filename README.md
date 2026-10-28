# Disk Image & Sparsebundle Recovery Tool

A lightweight **macOS utility** written in **Python** that attempts to unlock **macOS disk images** (`*.sparsebundle`, `*.dmg`, `*.sparseimage`) by testing candidate passwords from plain `.txt` wordlist files. This tool is intended for **legitimate data recovery** and **authorized digital forensics** when an encrypted disk image's password has been forgotten.

The tool automates `hdiutil attach` attempts, provides a live progress dashboard, and includes controls for managing recovery sessions. Recovery time varies depending on wordlist size, password complexity, disk image encryption, and hardware performance. Large dictionaries containing millions or billions of passwords can take a considerable amount of time to process.

---

## ⚙️ Brief Summary

* Attempts to unlock encrypted macOS disk images using candidate passwords supplied to `hdiutil`.
* Supports `.sparsebundle`, `.dmg`, and `.sparseimage` disk image formats.
* Automatically discovers supported disk images and `.txt` wordlists in the current working directory.
* Includes CrackStation's **Human Passwords Only** dictionary containing approximately 64 million passwords.
* Supports additional custom password dictionaries, including the full CrackStation dictionary when saved as a `.txt` file.
* Displays a live progress dashboard with password attempts, checking speed, elapsed time, and estimated completion time.
* Provides interactive controls to skip wordlists, skip disk images, or terminate the recovery process.
* Allows users to manually configure the order in which disk images are processed.
* Includes disk cleanup functionality to reduce attachment and detachment conflicts.
* Processes password dictionaries line by line without requiring the entire wordlist to be loaded into memory.

---

## ▶️ Run Script (3 Steps)

### 1) Download the Repository and Prepare Your Files

Clone the GitHub repository:

```bash
git clone https://github.com/Praetorian301/MacOS-DiskImage-Recovery-Tool.git
```

Navigate to the directory containing the Python script:

```bash
cd MacOS-DiskImage-Recovery-Tool/DiskImageCrackerMacOS
```

**Prepare the recovery environment:**

* Place encrypted disk images in the same directory as `cracker.py`.
* Supported formats include `.sparsebundle`, `.dmg`, and `.sparseimage`.
* Place any additional plain `.txt` password dictionaries in the same directory.
* The included `human.txt` dictionary contains approximately 64 million passwords collected from historical database breaches.
* Additional wordlists can be obtained from CrackStation, SecLists, Weakpass, and other publicly available sources.
* Password dictionaries are automatically discovered and processed by the script.

**Note:** The current script recognises `.txt` dictionaries only. If using the full CrackStation dictionary named `full.lst`, rename it to `full.txt` or modify the script to support `.lst` files.

### 2) Install Dependencies and Prepare Disk Cleanup

The utility requires **macOS**, **Python 3**, and the Python `rich` package.

Install the required Python dependency:

```bash
python3 -m pip install rich
```

The script uses the native macOS `hdiutil` utility to mount encrypted disk images and verify candidate passwords.

A disk cleanup helper can be used to detach mounted images that may interfere with password recovery attempts.

**Inspect currently attached disk images:**

```bash
hdiutil info
```

**Manually detach a specific disk image:**

```bash
hdiutil detach /dev/diskN
```

Replace `/dev/diskN` with the appropriate device identifier.

**Optional temporary `clean` alias:**

```bash
alias clean="hdiutil info | grep '/dev/disk' | awk '{print \$1}' | xargs -n1 sudo hdiutil detach -force"
```

**Dry run to inspect the devices matched by the alias:**

```bash
hdiutil info | grep '/dev/disk' | awk '{print $1}'
```

**Warning:** The `clean` alias may forcibly detach multiple mounted devices, including unrelated disk images. Inspect the devices before using it, and ensure no important volumes are in use.

### 3) Run the Recovery Script

From the `DiskImageCrackerMacOS` directory:

```bash
chmod +x ./cracker.py
python3 cracker.py
```

The script automatically identifies compatible disk images and available password dictionaries.

When prompted, press Enter to select **Mode 1, Local Wordlists**.

The utility will then display the discovered disk images and allow you to confirm or manually configure their processing order.

Once started, the script will test passwords from the available dictionaries against each selected disk image.

---

## 🔎 Process Overview

* Automatically scans the current directory for supported encrypted disk images and `.txt` password dictionaries.
* Detects available disk images and presents an optional manual ordering interface.
* Reads candidate passwords sequentially from each dictionary.
* Attempts to attach each encrypted image using the macOS `hdiutil` utility.
* Supplies candidate passwords through standard input using the `-stdinpass` argument.
* Monitors each `hdiutil` process to determine whether an attachment attempt was successful.
* Treats an exit code of `0` as a successful attachment.
* Displays a live dashboard containing the number of passwords checked, checking speed, elapsed time, and estimated completion time.
* Provides interactive keyboard controls:

  * `s` + Enter, skip the current password dictionary.
  * `b` + Enter, skip the current disk image.
  * `q` + Enter, terminate the recovery session.

* When a password is successfully identified, the utility displays the matching password and attempts to detach the mounted image.
* The script also performs disk cleanup operations during its execution.

---

## 🧠 Script Logic (Detailed)

1. **Discovery**
   * Locate supported disk image formats in the current working directory.
   * Identify all available `.txt` password dictionaries.
   * Sort detected wordlists by file size.

2. **Image Ordering**
   * Display all discovered disk images.
   * Allow automatic or manual selection of the processing order.
   * Confirm the final order before beginning recovery.

3. **Password Testing**
   * Read each password dictionary line by line.
   * Submit candidate passwords to `hdiutil attach` using `-stdinpass`.
   * Monitor the subprocess for successful or unsuccessful attachment.
   * Continue testing until a matching password is found or the dictionary is exhausted.

4. **Progress Monitoring**
   * Track the number of passwords tested.
   * Calculate an estimated checking rate.
   * Display progress and estimated completion time.
   * Warn users when the estimated processing time for a dictionary is unusually long.

5. **Interactive Controls**
   * `s` skips the active wordlist.
   * `b` skips the current disk image.
   * `q` terminates the recovery process.

6. **Successful Recovery**
   * Detect a successful `hdiutil` attachment.
   * Display the recovered password.
   * Report the time required to identify the password.
   * Attempt to detach the mounted volume.

7. **Cleanup**
   * Perform attachment cleanup operations.
   * Attempt to prevent leftover mounted images from interfering with subsequent tests.

---

## ⚠️ Troubleshooting

* **No supported disk images found:** Verify that `.sparsebundle`, `.dmg`, or `.sparseimage` files are located in the same directory as `cracker.py`.

* **No password dictionaries detected:** Ensure at least one `.txt` wordlist is present in the current working directory.

* **`full.lst` is not recognised:** The current script only discovers `.txt` files. Rename the dictionary to `full.txt` or extend the script's file discovery functionality.

* **Git LFS wordlist not downloaded:** Install Git LFS and run `git lfs pull` from the repository directory.

* **Python reports `ModuleNotFoundError: rich`:** Install the dependency using `python3 -m pip install rich`.

* **`hdiutil` is unavailable:** The recovery utility requires macOS and cannot run natively on Windows.

* **A device cannot be detached:** Check whether the disk image is being used by another application.

* **Extremely long estimated recovery time:** Large dictionaries may contain millions or billions of entries. Consider testing smaller, more targeted wordlists first.

* **An encrypted disk image cannot be unlocked:** Verify that the file is supported by `hdiutil` and that the correct password appears in the selected wordlist.

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
    │
    ├── cracker.py
    ├── Instructions.txt
    │
    ├── human.txt
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

**Notes:**

* `human.txt` is included in the GitHub repository through Git Large File Storage.
* `full.lst` is optional and is not included in the repository.
* The full dictionary must be renamed to `full.txt` for compatibility with the current script.
* Additional disk images and wordlists can be added to the working directory.
* The contents of individual `.sparsebundle` directories may vary.

---

## 📚 Password Dictionaries & Wordlists

The utility supports plaintext password dictionaries and includes a CrackStation dictionary for password recovery testing.

### CrackStation Human Passwords Only, `human.txt`

The repository includes CrackStation's smaller **Human Passwords Only** wordlist.

This dictionary contains approximately **64 million real passwords** collected from historical website database breaches.

Unlike the complete CrackStation dictionary, this collection focuses specifically on passwords obtained from leaked password databases rather than general dictionary words and other text sources.

| Property | Details |
|---|---|
| Filename | `human.txt` |
| Passwords | Approximately 64 million |
| Uncompressed size | Approximately 684 MiB |
| Original compressed size | Approximately 247 MiB |
| Format | Plain text, one password per line |
| GitHub storage | Git LFS |
| Source | CrackStation |
| License | CC BY-SA 3.0 |

**Original download:** [CrackStation Human Passwords Only](https://crackstation.net/files/crackstation-human-only.txt.gz)

**SHA256 of the original compressed archive:**

```text
201f8815c71a47d39775304aa422a505fc4cca18493cfaf5a76e608a72920267
```

### CrackStation Full Password Dictionary, `full.lst`

CrackStation also provides a significantly larger password dictionary containing approximately **1.49 billion entries**.

The complete dictionary incorporates:

* Historical leaked password databases.
* Public password dictionaries and wordlists.
* Wikipedia article text from multiple languages.
* Public domain books and other textual sources.
* Additional password collections gathered from historical data breaches.

| Property | Details |
|---|---|
| Local filename | `full.lst` |
| Entries | 1,493,677,782 |
| Uncompressed size | Approximately 15 GiB |
| Original compressed size | Approximately 4.2 GiB |
| Format | Plain text |
| Repository status | Not included |
| Source | CrackStation |
| License | CC BY-SA 3.0 |

**Original download:** [CrackStation Full Dictionary](https://crackstation.net/files/crackstation.txt.gz)

**SHA256 of the original compressed archive:**

```text
a6dc17d27d0a34f57c989741acdd485b8aee45a6e9796daf8c9435370dc61612
```

The complete dictionary is not bundled with this repository due to its substantial size.

Users wishing to use the complete dictionary can download it separately, extract it, and place it in the same directory as `cracker.py`.

**Important:** Rename `full.lst` to `full.txt` before using it with the current script.

### Additional Wordlist Sources

* [CrackStation](https://crackstation.net/crackstation-wordlist-password-cracking-dictionary.htm)
* [SecLists, GitHub](https://github.com/danielmiessler/SecLists)
* [Weakpass](https://weakpass.com/)

Only use password dictionaries in circumstances where you have permission to conduct recovery or security testing.

### Git Large File Storage

The included `human.txt` dictionary is stored using **Git LFS** because it exceeds GitHub's standard file size limit.

Install Git LFS before cloning the repository:

```bash
git lfs install
```

Clone the repository normally:

```bash
git clone https://github.com/Praetorian301/MacOS-DiskImage-Recovery-Tool.git
```

If the dictionary was not automatically downloaded, run:

```bash
cd MacOS-DiskImage-Recovery-Tool
git lfs pull
```

Git LFS downloads the dictionary's actual contents rather than leaving only the small pointer file.

---

## ⚖️ Warnings & Legal

* **Authorized use only.** This utility is intended for disk images you own or are explicitly authorised to examine.
* Password recovery operations must comply with applicable laws, organisational policies, and access permissions.
* Unauthorized access to systems, devices, or data may constitute a criminal offence.
* The utility performs repeated password attempts against encrypted disk images and should not be used against systems without permission.
* Disk cleanup operations may forcibly detach mounted volumes. Exercise caution when using privileged commands.
* If sensitive information or credentials are exposed during authorised recovery work, handle them securely.

---

## 🧾 Notes & Limitations

* Password recovery success depends on whether the correct password appears in the supplied wordlists.
* Large dictionaries may require substantial processing time.
* Performance depends on available hardware resources, encryption configuration, and the overhead of repeatedly invoking `hdiutil`.
* The current implementation tests passwords individually rather than using GPU acceleration or specialised offline cracking engines.
* The progress dashboard displays estimated checking rates and completion times, which may fluctuate.
* The script currently supports plaintext `.txt` password dictionaries.
* The complete CrackStation dictionary is not included due to its storage requirements.
* The utility relies on macOS `hdiutil` and is not designed to run natively on Windows or Linux.
* Certain disk image encryption configurations may prevent recovery through simple dictionary testing.
* The script's disk cleanup functionality may interfere with unrelated mounted volumes.

---

## 👨‍💻 Credits & Contact

Created and maintained by **[@Praetorian301](https://github.com/Praetorian301)**.

**Password Dictionary Attribution:**

CrackStation password dictionaries are provided by [CrackStation](https://crackstation.net/), developed by Defuse Security.

The CrackStation dictionaries are distributed under the [Creative Commons Attribution ShareAlike 3.0 License](https://creativecommons.org/licenses/by-sa/3.0/).

Additional password dictionary resources include SecLists and Weakpass.

**Repository:** [MacOS Disk Image Recovery Tool](https://github.com/Praetorian301/MacOS-DiskImage-Recovery-Tool)

---
