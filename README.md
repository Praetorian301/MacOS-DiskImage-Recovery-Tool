Sparsebundle / Disk Image Recovery Tool
======================================

What this is
------------
A small macOS utility (Python 3) that attempts to unlock disk images
(`*.sparsebundle`, `*.dmg`, `*.sparseimage`) using candidate passwords
from plain `.txt` wordlist files. Intended for legitimate data recovery
and authorized digital-forensics work.

What it does (brief)
--------------------
- Scans the repository folder for supported disk images and `*.txt` wordlists.
- For each image it attempts to attach the image using `hdiutil`, sending
  candidate passwords to `hdiutil` via stdin.
- Shows a live progress dashboard (checked count, rate, ETA) and accepts
  simple keyboard commands to control the run.
- Includes a helper `clean` command to detach currently mounted disks to
  avoid attach/detach conflicts.

Key script logic (high level)
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

Quick start (3 steps)
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

   Or run both:
     clean && python3 cracker.py
     # or if using the simplified name:
     clean && python3 cracker_mode1_only.py

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

Safety, size & git advice
-------------------------
- Do NOT commit large binary images or private data. Add this to `.gitignore`:
  *.dmg
  *.sparsebundle
  *.sparseimage
  .DS_Store
  .venv/
  __pycache__/

- Prefer including a small generator script (make_test_bundles.sh) to create demo images locally rather than storing them in Git history.
- If you accidentally push large files, remove them from history with `git filter-repo` or BFG and consider rotating any exposed credentials.

Credits
-------
Small public wordlists may be included for convenience. Credit: SecLists, Weakpass, and other open sources.

Warnings & legal
----------------
- Authorized use only: run this tool only on images you own or have explicit permission to test.
- `clean` uses `sudo` and forcibly detaches volumes — use with care.
- Unauthorized access to systems or data is illegal.

Want extras?
------------
If you want, I can:
- provide a `make_test_bundles.sh` generator script (recommended),
- add a ready-to-paste `.gitignore` into the repo,
- or produce a minimal `README.md` version for GitHub display.
