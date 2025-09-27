Cracker Script — README
=======================

What this is
------------
This is a small macOS utility that tries to unlock .sparsebundle disk images using candidate passwords found in plain .txt wordlist files. It is intended to help with legitimate digital forensics or data recovery scenarios.


Quick start (3 steps)
---------------------
1. Put your files in the repo:
   • Add any `.sparsebundle` files to the repository root (e.g. `test.sparsebundle`, `aaronite.sparsebundle`).
   • Add any `.txt` wordlists to the same folder (Mode 1 will automatically find them). 
   • Download .txt files sites like https://weakpass.com and https://github.com/danielmiessler/SecLists/


2. Make the `clean` helper command available (recommended):
   • Open a command terminal in the root directory and paste this line:
     
     alias clean="hdiutil info | grep '/dev/disk' | awk '{print \$1}' | xargs -n1 sudo hdiutil detach -force"
     
     It finds device nodes listed by `hdiutil` and force-detaches them to ensure the program runs properly.
     
     If you just want to see what would be detached (dry run), run: hdiutil info | grep '/dev/disk' | awk '{print $1}'


3. Run the tool:
   From the repository root (where your `.sparsebundle` files are):
     
     clean
     python3 cracker.py
     
   Or run both at once:
     
     clean && python3 cracker.py


     

Where to put wordlists and bundles
---------------------------------
• `.sparsebundle` files → repo root (same folder as the script).  
• `.txt` wordlists → repo root (Mode 1 auto-discovers `*.txt` files).

Notes, troubleshooting, and tips
-------------------------------
• If the script reports “No .sparsebundle files found”, check that the files are in the repo root and end with `.sparsebundle`.  
• If `clean` prints nothing, there are no mounted `/dev/disk` entries to detach.  
• If a device won’t detach, check which process is using it (or reboot). 
• Manually, eject all sparse bundle disk images before running the ./cracker command.  
• You can run `clean` safely before each run to auto reduce these attach/detach problems.

Credits
-------
Some common wordlists are included. Credit: public collections such as SecLists and other open sources.

Warnings & legal
----------------
• `clean` uses `sudo` and forcibly detaches volumes — use with care.  
• Do not run this tool on systems or images you do not own or are not explicitly authorized to test.  
• Unauthorized access to systems or data is illegal.
