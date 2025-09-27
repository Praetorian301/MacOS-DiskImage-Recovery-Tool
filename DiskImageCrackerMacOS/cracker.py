#!/usr/bin/env python3
import subprocess, time, os, glob, sys, gzip, shutil, urllib.request, multiprocessing, threading, termios, tty, select
from threading import Event
from datetime import timedelta
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.live import Live
from rich.panel import Panel

console = Console()

# ========================= Config =========================
CPU_CORES = multiprocessing.cpu_count()
MAX_WORKERS = max(4, CPU_CORES // 2)
DETACH_SWEEP = r"hdiutil info | grep '/dev/disk' | awk '{print $1}' | xargs -n1 sudo hdiutil detach -force"
ATTACH_POLL_INTERVAL = 0.05
ATTACH_KILL_GRACE = 0.5
ETA_THRESHOLD_SECS = 120
DEFAULT_RATE = 12.0
WORDLISTS_FOLDER = "wordlists"
SUPPORTED_IMAGE_GLOBS = ["*.sparsebundle", "*.dmg", "*.sparseimage"]


# ========================= Input watcher (simple line-based) =========================
class InputWatcher:
    def __init__(self):
        self.skip_file = Event()
        self.skip_bundle = Event()
        self.quit_all = Event()
        self._stop = Event()
        self._t = threading.Thread(target=self._loop, daemon=True)

    def start(self):
        self._t.start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        while not self._stop.is_set():
            try:
                r, _, _ = select.select([sys.stdin], [], [], 0.1)
                if r:
                    line = sys.stdin.readline().strip().lower()
                    if line == "s":
                        self.skip_file.set()
                    elif line == "b":
                        self.skip_bundle.set()
                    elif line == "q":
                        self.quit_all.set()
                        self._stop.set()
                        break
            except Exception:
                time.sleep(0.1)


# ========================= Utilities =======================

def human_int(n: int) -> str:
    return f"{n:,}"


def human_size(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    s = float(n)
    for u in units:
        if s < 1024.0:
            return f"{s:.1f}{u}"
        s /= 1024.0
    return f"{s:.1f}PB"


def run_shell(cmd: str):
    return subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def clean_mounts():
    console.print("[yellow][*] Cleaning up mounted disks before starting...[/yellow]")
    run_shell(DETACH_SWEEP)


# discover images: sparsebundle, dmg, sparseimage
def discover_images():
    files = []
    for g in SUPPORTED_IMAGE_GLOBS:
        files.extend(glob.glob(g))
    return sorted(files)


def discover_password_files():
    local = glob.glob("*.txt")
    return sorted(local, key=lambda f: os.path.getsize(f))


# ---------- Modes ----------

def get_mode() -> int:
    # Only Mode 1 is supported now
    console.rule("[bold cyan]Cracking Mode: Local Wordlists")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Mode", style="cyan")
    table.add_column("Description", style="white")
    table.add_row("1", "Local Wordlists (.txt in current folder)")
    console.print(table)
    # Keep compatibility with existing flow: accept Enter or '1'
    while True:
        choice = input("Press Enter to use Mode 1 (Local Wordlists) or type '1' then Enter: ").strip()
        if choice == "" or choice == "1":
            return 1


# ---------- Wordlist helpers (left available if needed) ----------

def _decompress_gz_if_needed(path: str) -> str:
    if not path.endswith(".gz"):
        return path
    out = path[:-3]
    if os.path.exists(out) and os.path.getsize(out) > 0:
        return out
    console.print(f"[yellow][*] Decompressing {os.path.basename(path)} → {os.path.basename(out)}[/yellow]")
    with gzip.open(path, "rb") as f_in, open(out, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    return out


# (ensure_remote_wordlists and generator left in place but unused in Mode 1)

def ensure_remote_wordlists():
    os.makedirs(WORDLISTS_FOLDER, exist_ok=True)
    lists = []
    # REMOTE_LISTS expected to be provided elsewhere if ever used
    try:
        for fname, url in REMOTE_LISTS.items():
            dest = os.path.join(WORDLISTS_FOLDER, fname)
            if not os.path.exists(dest):
                console.print(f"[yellow][*] Downloading {fname}...[/yellow]")
                urllib.request.urlretrieve(url, dest)
            lists.append(dest)
    except NameError:
        # No remote lists configured
        pass
    expanded = [_decompress_gz_if_needed(p) for p in lists]
    expanded.extend(glob.glob(os.path.join(WORDLISTS_FOLDER, "*.txt")))
    seen, dedup = set(), []
    for p in expanded:
        if p not in seen:
            seen.add(p)
            dedup.append(p)
    return sorted(dedup, key=lambda f: os.path.getsize(f))


def generate_candidates():
    words = ["smash", "power", "secret", "apple", "dragon", "hunter"]
    suffixes = ["", "1", "12", "123", "!", "2024", "2025"]
    for w in words:
        for sfx in suffixes:
            yield f"{w}{sfx}".encode()
            yield f"{w.capitalize()}{sfx}".encode()
    for w1 in words:
        for w2 in words:
            if w1 == w2:
                continue
            yield f"{w1}{w2}".encode()
            yield f"{w1}-{w2}".encode()
            yield f"{w1}{w2}123".encode()


# ---------- Attach attempt (INTERRUPTIBLE) ----------

def safe_detach_volume_from_image(image_path):
    # determine a reasonable volume name guess from filename
    base = os.path.basename(image_path)
    for ext in ('.sparsebundle', '.dmg', '.sparseimage'):
        if base.lower().endswith(ext):
            name = base[:-len(ext)]
            break
    else:
        name = os.path.splitext(base)[0]
    vol = f"/Volumes/{name}"
    subprocess.run(["hdiutil", "detach", vol], stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _terminate_proc(proc: subprocess.Popen):
    try:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=ATTACH_KILL_GRACE)
            except subprocess.TimeoutExpired:
                proc.kill()
    except Exception:
        pass
    run_shell(DETACH_SWEEP)


def try_password_interruptible(image_path, pwd_bytes: bytes, watcher: InputWatcher, stop_event: Event):
    if stop_event.is_set():
        return ("ok", False)
    # Use hdiutil attach; works for sparsebundle, dmg, sparseimage.
    proc = subprocess.Popen(
        ["hdiutil", "attach", image_path, "-stdinpass", "-nobrowse", "-quiet", "-readonly", "-noverify"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    try:
        try:
            proc.stdin.write(pwd_bytes)
            proc.stdin.flush()
        except Exception:
            pass
        finally:
            try:
                proc.stdin.close()
            except Exception:
                pass
        while True:
            rc = proc.poll()
            if rc is not None:
                return ("ok", rc == 0)
            if watcher.quit_all.is_set():
                _terminate_proc(proc)
                return ("quit", False)
            if watcher.skip_bundle.is_set():
                _terminate_proc(proc)
                return ("skip_bundle", False)
            if watcher.skip_file.is_set():
                _terminate_proc(proc)
                return ("skip_file", False)
            if stop_event.is_set():
                _terminate_proc(proc)
                return ("ok", False)
            time.sleep(ATTACH_POLL_INTERVAL)
    finally:
        try:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=ATTACH_KILL_GRACE)
                except subprocess.TimeoutExpired:
                    proc.kill()
        except Exception:
            pass


# ---------- Helpers ----------

def estimate_line_count_fast(path: str, sample_bytes: int = 1_000_000) -> int:
    try:
        total_size = os.path.getsize(path)
        if total_size == 0:
            return 0
        with open(path, "rb") as f:
            chunk = f.read(min(sample_bytes, total_size))
            if not chunk:
                return 0
            nl = chunk.count(b"\n")
            if nl == 0:
                avg = 10.0
            else:
                avg = len(chunk) / nl
            estimate = int(max(1, total_size / max(1.0, avg)))
            return estimate
    except Exception:
        return 0


def count_lines_exact_if_small(path: str, size_threshold_bytes: int = 5_000_000) -> int:
    try:
        if os.path.getsize(path) <= size_threshold_bytes:
            with open(path, "rb") as f:
                return sum(1 for _ in f)
        else:
            return estimate_line_count_fast(path)
    except FileNotFoundError:
        return 0


def load_file_binary_lines(path):
    with open(path, "rb") as f:
        for raw in f:
            pwd = raw.rstrip(b"\r\n")
            if pwd:
                yield pwd


def make_dashboard(bundle, label, dash):
    rate = dash["checked"] / max(time.time() - dash["start"], 1)
    todo = max(dash["total"] - dash["checked"], 0)
    eta = (todo / rate) if rate > 0 else 0
    body = f"""
    [cyan]Image:[/cyan] {bundle}
    [yellow]Source:[/yellow] {os.path.basename(label)}
    [green]Checked:[/green] {human_int(dash['checked'])} / {human_int(dash['total'])}
    [magenta]Rate:[/magenta] {rate:.1f}/sec
    [blue]ETA:[/blue] {str(timedelta(seconds=int(eta)))}
    """
    return Panel(body, title="Cracker Status", border_style="bold blue")


# ---------- Long ETA prompt with countdown ----------

def prompt_skip_or_jump_if_slow(current_idx: int, sources: list, sizes_bytes: list, eta_seconds: float):
    if eta_seconds <= ETA_THRESHOLD_SECS:
        return "continue"
    console.rule("[bold yellow]Long ETA Detected")
    console.print(f"[yellow]Estimated time for current file: {str(timedelta(seconds=int(eta_seconds)))} (> 2 minutes).[/yellow]")
    console.print("[cyan]Press Enter to continue, type 's' to skip, or enter a number to jump.[/cyan]")
    tbl = Table(show_header=True, header_style="bold magenta")
    tbl.add_column("#", justify="right", style="cyan", no_wrap=True)
    tbl.add_column("Wordlist", style="white")
    tbl.add_column("Size", justify="right", style="green")
    for i, src in enumerate(sources, start=1):
        fname = os.path.basename(src)
        sz = sizes_bytes[i - 1]
        marker = " " if (i - 1) != current_idx else "→ "
        tbl.add_row(str(i), f"{marker}{fname}", human_size(sz))
    console.print(tbl)

    countdown = min(30, max(5, int(eta_seconds))) if eta_seconds >= 5 else 5
    countdown = min(30, countdown)

    start = time.time()
    remaining = countdown
    printed_notices = []
    if countdown >= 30:
        console.print(f"[dim]You have [bold yellow]30s[/bold yellow] to choose...[/dim]")
        printed_notices.append(30)
    if countdown >= 20 and 20 not in printed_notices:
        console.print(f"[dim]You have [bold yellow]20s[/bold yellow] to choose...[/dim]")
        printed_notices.append(20)
    last_notice = printed_notices[-1] if printed_notices else None

    while True:
        try:
            r, _, _ = select.select([sys.stdin], [], [], 1.0)
            if r:
                ans = sys.stdin.readline().strip().lower()
                if ans == "":
                    return "continue"
                if ans == "s":
                    return "skip"
                try:
                    jump = int(ans)
                    if 1 <= jump <= len(sources):
                        return jump - 1
                    else:
                        console.print(f"[red]Please enter a number 1–{len(sources)}.[/red]")
                except ValueError:
                    console.print("Invalid input. Enter nothing, 's', or a number.")
            elapsed = int(time.time() - start)
            remaining = countdown - elapsed
            if remaining <= 0:
                console.print("[dim]No input — continuing.[/dim]")
                return "continue"
            if remaining % 10 == 0 and remaining != last_notice:
                console.print(f"[dim]You have [bold yellow]{remaining}s[/bold yellow] to choose...[/dim]")
                last_notice = remaining
        except KeyboardInterrupt:
            console.print("[dim]Interrupted — continuing.[/dim]")
            return "continue"


# ---------- Cracking one image ----------

def crack_bundle(bundle, sources, mode, watcher: InputWatcher):
    console.rule(f"[bold green]Starting: {bundle}")
    safe_detach_volume_from_image(bundle)
    run_shell(DETACH_SWEEP)

    run_start = time.time()
    bundle_checked = 0
    processed = [False] * len(sources)
    sizes_bytes = [os.path.getsize(s) if os.path.exists(s) else 0 for s in sources]

    with Progress(
        SpinnerColumn(), BarColumn(), "[progress.percentage]{task.percentage:>3.0f}%",
        TextColumn("{task.description}"), TimeElapsedColumn(), TimeRemainingColumn(),
        console=console, transient=True,
    ) as progress:
        i = 0
        while i < len(sources):
            while i < len(sources) and processed[i]:
                i += 1
            if i >= len(sources):
                break
            if watcher.quit_all.is_set():
                return "quit"
            if watcher.skip_bundle.is_set():
                console.print("[yellow][!] Skipping bundle by request.[/yellow]")
                watcher.skip_bundle.clear()
                return "skipped_bundle"

            source = sources[i]
            est_lines = estimate_line_count_fast(source)
            elapsed = max(0.0001, time.time() - run_start)
            rate = max(DEFAULT_RATE, bundle_checked / elapsed)
            eta_seconds = est_lines / max(rate, 0.0001)
            decision = prompt_skip_or_jump_if_slow(i, sources, sizes_bytes, eta_seconds)
            if decision == "skip":
                console.print(f"[yellow][!] Skipping {source} by request.[/yellow]")
                processed[i] = True
                continue
            elif isinstance(decision, int):
                i = decision
                continue

            total_for_bar = count_lines_exact_if_small(source)
            if total_for_bar <= 0:
                processed[i] = True
                i += 1
                continue
            candidates = load_file_binary_lines(source)
            label = source

            console.print(f"[blue][*] Using source {source} ({human_int(total_for_bar)} entries)[/blue]")
            task = progress.add_task(f"[cyan]{os.path.basename(label)}", total=total_for_bar)
            dash = {"start": time.time(), "checked": 0, "total": total_for_bar}
            found_event = Event()
            with Live(make_dashboard(bundle, label, dash), refresh_per_second=8, console=console) as live:
                for pwd in candidates:
                    if watcher.quit_all.is_set():
                        return "quit"
                    if watcher.skip_bundle.is_set():
                        console.print("[yellow][!] Skipping bundle by request.[/yellow]")
                        watcher.skip_bundle.clear()
                        return "skipped_bundle"
                    if watcher.skip_file.is_set():
                        console.print("[yellow][!] Skipping current source by request.[/yellow]")
                        watcher.skip_file.clear()
                        break

                    status, ok = try_password_interruptible(bundle, pwd, watcher, found_event)
                    if status == "quit":
                        return "quit"
                    if status == "skip_bundle":
                        console.print("[yellow][!] Skipping bundle by request.[/yellow]")
                        watcher.skip_bundle.clear()
                        return "skipped_bundle"
                    if status == "skip_file":
                        console.print("[yellow][!] Skipping current source by request.[/yellow]")
                        break

                    dash["checked"] += 1
                    progress.update(task, advance=1)
                    live.update(make_dashboard(bundle, label, dash))

                    if ok:
                        elapsed = time.time() - run_start
                        console.rule("[bold green]SUCCESS")
                        try:
                            shown = pwd.decode("utf-8")
                        except UnicodeDecodeError:
                            shown = None
                        if shown:
                            console.print(f"[bold green][+] PASSWORD FOUND:[/bold green] [white on green]{shown}[/white on green]")
                        console.print(f"[bold green][+] BYTES:[/bold green] {pwd!r}")
                        console.print(f"[bold green][+] Time:[/bold green] {elapsed:.1f}s")
                        safe_detach_volume_from_image(bundle)
                        run_shell(DETACH_SWEEP)
                        return "found"

            processed[i] = True
            bundle_checked += dash["checked"]
            i += 1

    console.rule("[bold red]No Match")
    console.print(f"[red][-] No match for {bundle}.[/red]")
    return "no_match"


# ---------- Bundle order UI ----------

def choose_bundle_order(bundles):
    console.rule("[bold cyan]Bundle Ordering")
    auto_table = Table(show_header=True, header_style="bold magenta")
    auto_table.add_column("#", justify="right", style="cyan", no_wrap=True)
    auto_table.add_column("Bundle", style="white")
    for i, b in enumerate(bundles, start=1):
        auto_table.add_row(str(i), b)
    console.print(auto_table)
    resp = input("Press Enter to keep this auto order, or type 'm' to manually reorder: ").strip().lower()
    if resp not in ("m", "manual", "y", "yes"):
        return bundles[:]

    n = len(bundles)
    assigned, used = {}, set()
    for idx, b in enumerate(bundles, start=1):
        while True:
            default_pos = idx
            raw = input(f"Position for {b} (1–{n}) [Enter for {default_pos}]: ").strip()
            if raw == "":
                pos = default_pos
            else:
                try:
                    pos = int(raw)
                except Exception:
                    console.print("[red]Please enter a number.[/red]")
                    continue
            if not (1 <= pos <= n):
                console.print(f"[red]Invalid position (1–{n}).[/red]")
                continue
            if pos in used:
                console.print(f"[red]Position {pos} already taken.[/red]")
                continue
            assigned[b] = pos
            used.add(pos)
            break

    ordered = [None] * n
    for b, p in assigned.items():
        ordered[p - 1] = b
    ordered = [b for b in ordered if b is not None]

    final = Table(show_header=True, header_style="bold green")
    final.add_column("Order", justify="right", style="green", no_wrap=True)
    final.add_column("Bundle", style="white")
    for i, b in enumerate(ordered, start=1):
        final.add_row(str(i), b)
    console.print(final)
    confirm = input("Press Enter to confirm this order, or type 'r' to redo: ").strip().lower()
    if confirm in ("r", "redo"):
        return choose_bundle_order(bundles)
    return ordered


# ============================= Main =============================
if __name__ == "__main__":
    clean_mounts()
    # Mode selection reduced to Mode 1 only
    mode = get_mode()
    bundles = discover_images()
    if not bundles:
        console.print("[red]No supported disk images (.sparsebundle, .dmg, .sparseimage) found in this folder.[/red]")
        sys.exit(1)

    # Only Local Wordlists mode is available
    sources = discover_password_files()

    if not sources:
        console.print("[red]No sources found for this mode.[/red]")
        sys.exit(1)

    # Decide bundle order (manual or auto)
    ordered = choose_bundle_order(bundles)

    console.rule("[bold cyan]Summary")
    console.print(f"[cyan]Mode:[/cyan] 1 (Local Wordlists)")
    console.print(f"[cyan]Detected {len(bundles)} images[/cyan]")
    console.print(f"[cyan]Sources:[/cyan] {sources}")

    watcher = InputWatcher()
    watcher.start()
    try:
        for b in ordered:
            if watcher.quit_all.is_set():
                break
            crack_bundle(b, sources, mode, watcher)
    finally:
        watcher.stop()
