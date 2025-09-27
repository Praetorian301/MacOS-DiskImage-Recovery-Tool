Sparsebundle & Disk Image Recovery Tool
======================================

Brief Summary
------------
A lightweight macOS utility written in Python, this script attempts to unlock macOS disk images (*.sparsebundle, *.dmg, *.sparseimage) using candidate passwords from plain .txt wordlist files. It is intended for legitimate data recovery and authorized digital-forensics work when an image’s password has been forgotten. The tool automates hdiutil attach attempts, provides a live progress dashboard, and includes helper commands to avoid attach/detach conflicts. Depending on wordlist size and your machine, it may recover access in a few hours for small lists, but large wordlists can take much longer.

Process Overview
--------------------
- Auto scans the repository folder for supported disk images and `*.txt` wordlists.
- For each image it attempts to attach the image using `hdiutil`, sending
  candidate passwords to `hdiutil` via stdin.
- Shows a live progress dashboard (checked count, rate, ETA) and accepts
  simple keyboard commands to control the run.
- Includes a helper `clean` command to detach currently mounted disks to
  avoid attach/detach conflicts.

Script Logic
-----------------------------
1. Discovery — find disk images in the repo root and `*.txt` wordlists (Mode 1).
2. Order — present an order of images (auto or manual reorder).
3. For each image:
   - Try passwords from each selected wordlist line-by-line.
   - Use `hdiutil attach <image> -stdinpass ...` so the password is provided programmatically.
   - Monitor the `hdiutil` process; exit code 0 means the attach succeeded (password found).
4. Interrupts & controls:
   - Type `s` + Enter to skip current wordlist (file).
   - Type `b` + Enter to skip current image/bundle.
   - Type `q` + Enter to quit the run.
5. Cleanup — on success or exit the script attempts to detach mounted volumes and runs a detach sweep.

Quick Start (3 steps)
---------------------
1) Add your files:
   - Put your disk images in the repo root (examples: test.sparsebundle, test.dmg).
   - Put `.txt` wordlists in the same folder (Mode 1 auto-discovers them).
   - Use public, legal wordlists (e.g., SecLists, Weakpass) — only use lists you are allowed to use.

2) Make the `clean` helper available (recommended):
   - Temporary alias (paste in terminal):
     alias clean="hdiutil info | grep '/dev/disk' | awk '{print \$1}' | xargs -n1 sudo hdiutil detach -force"

   - Dry run (see devices that would be detached):
     hdiutil info | grep '/dev/disk' | awk '{print $1}'

   - Optional safer function (add to ~/.bashrc or ~/.zshrc):
     clean() {
       echo "Devices to detach:"
       hdiutil info | grep '/dev/disk' | awk '{print $1}'
       echo
       echo "Detaching (you may be prompted for your password)..."
       hdiutil info | grep '/dev/disk' | awk '{print $1}' | xargs -n1 sudo hdiutil detach -force
     }

3) Run the tool:
   From the repository root:
     clean
     python3 cracker.py

Where to put wordlists and bundles
---------------------------------
- Disk images: repo root (same folder as the script).
- Wordlists: `.txt` files in the repo root. Mode 1 detects `*.txt` automatically.

What to expect / controls
-------------------------
- The script shows a progress bar and live dashboard with ETA.
- Large wordlists may take a long time; the script will prompt if a file looks slow.
- Controls while running: `s` (skip file), `b` (skip image), `q` (quit) — press Enter after the key.

Troubleshooting
---------------
- “No `.sparsebundle` files found” — check that the images are in the repo root and named correctly.
- If `clean` prints nothing — there are no mounted `/dev/disk` entries to detach.
- If a device won’t detach, check which process is using it or reboot.
- If `hdiutil` attach behaves differently for a specific image type, test `hdiutil` manually.

Credits
-------
Small public wordlists may be included for convenience. Credit: SecLists, Weakpass, and other open sources.

Warnings & legal
----------------
- Authorized use only: run this tool only on images you own or have explicit permission to test.
- `clean` uses `sudo` and forcibly detaches volumes — use with care.
- Unauthorized access to systems or data is illegal.
