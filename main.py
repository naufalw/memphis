import argparse
import os
import re
import subprocess
import sys
import tempfile
import termios
import tty
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from io import TextIOWrapper

# ===== AESTHETICS ======

GRN = "\033[92m"
CYN = "\033[96m"
YEL = "\033[93m"
DIM = "\033[2m"
R = "\033[0m"


def fmt_byte(b: int, char_mode: bool = False) -> str:
    if b == 0:
        return f"{DIM} \\0{R}"

    if char_mode:
        return f"{YEL}{chr(b).center(3)}{R}"

    return f"{YEL}{b:3d}{R}"


def render_var(var, raw, top_bar=True):
    name = var["name"]
    typ = var["type"]
    size = var["size"]
    is_char = "char" in typ

    if top_bar:
        print("  " + "-" * 70)
    print(f"  {CYN}{name}{R}" + f" {typ} ({size} bytes)")

    max_cols = 8
    separator = f" {DIM}│{R} "
    rows = [raw[i : i + max_cols] for i in range(0, len(raw), max_cols)]
    base = int(var["addr"], 16)

    first_addr = hex(base)
    pad = " " * (2 + len(first_addr) + 3)
    ruler = "".join(
        f"{('+' + str(i)).center(3)}   " for i in range(min(max_cols, len(raw)))
    )
    print(f"{pad}{ruler}")

    for ri, row in enumerate(rows):
        row_addr = hex(base + ri * max_cols)
        cells = separator.join(fmt_byte(b, is_char) for b in row)
        print(f"  {row_addr} │ {cells} │")


def read_key() -> str:
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ===== GDB Wrapper ======
class GDB:
    """
    GDB wrapper hehe.
    """

    def __init__(self, binary: str) -> None:
        self.proc = subprocess.Popen(
            ["gdb", "--interpreter=mi2", "--quiet", binary],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        assert self.proc.stdin is not None
        assert self.proc.stdout is not None
        self.stdin: TextIOWrapper = self.proc.stdin  # type: ignore[assignment]
        self.stdout: TextIOWrapper = self.proc.stdout  # type: ignore[assignment]
        self._drain()

    def _readline(self) -> str:
        "Read output line from gdb"
        while True:
            line = self.stdout.readline()
            if line:
                return line.strip()

    def _drain(self) -> None:
        "Drain unnecessary yap from gdb"
        while True:
            if self._readline().startswith("(gdb)"):
                return

    def cmd(self, c: str) -> list[str]:
        """for commands ends with (gdb)"""
        self.stdin.write(c + "\n")
        self.stdin.flush()
        lines: list[str] = []
        while True:
            line = self._readline()
            if line.startswith("(gdb)"):
                return lines
            lines.append(line)

    def run_cmd(self, c: str) -> list[str]:
        """for commands ends with *stopped"""
        self.stdin.write(c + "\n")
        self.stdin.flush()
        lines: list[str] = []
        while True:
            line = self._readline()
            lines.append(line)
            if line.startswith("*stopped"):
                self._drain()
                return lines

    def close(self) -> None:
        try:
            self.stdin.write("-gdb-exit\n")
            self.stdin.flush()
        except Exception:
            pass
        self.proc.terminate()


# ==== GDB PARSER ======


def parse_addr(raw: str) -> str | None:
    m = re.search(r"\$\d+ = (0x[0-9a-f]+)", raw)
    return m.group(1) if m else None


def parse_type(raw: str) -> str | None:
    m = re.search(r"type = ([^\\]+)", raw)
    return m.group(1).strip() if m else None


def parse_size(raw: str) -> int | None:
    m = re.search(r"\$\d+ = (\d+)", raw)
    return int(m.group(1)) if m else None


def read_bytes(gdb: GDB, addr: str, size: int) -> list[int]:
    out = " ".join(gdb.cmd(f"-data-read-memory-bytes {addr} {size}"))
    m = re.search(r'contents="([0-9a-f]+)"', out)
    if not m:
        return []
    hex_str = m.group(1)
    return [int(hex_str[i : i + 2], 16) for i in range(0, len(hex_str), 2)]


def is_pointer(typ: str) -> bool:
    return typ.strip().endswith("*")


def read_pointer(gdb: GDB, addr: str) -> str | None:
    out = " ".join(gdb.cmd(f"print/x *((unsigned long long *){addr})"))
    m = re.search(r"\$\d+ = (0x[0-9a-f]+)", out)
    return m.group(1) if m else None


def heap_size(gdb: GDB, addr: str) -> int | None:
    out = " ".join(gdb.cmd(f"print (size_t)malloc_usable_size((void*){addr})"))
    m = re.search(r"\$\d+ = (\d+)", out)
    size = int(m.group(1)) if m else 0
    return size if size > 0 else None


def is_heap_address(addr: str) -> bool:
    val = int(addr, 16)
    return val < 0x7F0000000000


def snapshot(gdb, variables):
    print("\033[2J\033[3J\033[H", end="", flush=True)
    fname, func, lineno, src = current_line(gdb)
    print(f"\n  {fname}  {func}()  line {lineno}")
    print(f"  ▶  {src}\n")
    for var in variables:
        raw = read_bytes(gdb, var["addr"], var["size"])
        render_var(var, raw)

        if is_pointer(var["type"]):
            target = read_pointer(gdb, var["addr"])
            if target:
                print(f"  Points to ──→  {target}")
                if is_heap_address(target):
                    hsize = heap_size(gdb, target)
                    if hsize:
                        print(
                            f"\n{GRN}  [HEAP {target}]{R}  {hsize} bytes  ←── {var['name']}",
                        )
                        heap_raw = read_bytes(gdb, target, hsize)
                        render_var(
                            {
                                "name": "",
                                "addr": target,
                                "type": var["type"],
                                "size": hsize,
                            },
                            heap_raw,
                            top_bar=False,
                        )
                        print("  " + "-" * 70)

    print("\n  n=next  q=quit  s=step  r=next-breakpoint")


def current_line(gdb):
    frame = " ".join(gdb.cmd("-stack-info-frame"))
    line_m = re.search(r'line="(\d+)"', frame)
    file_m = re.search(r'file="([^"]+)"', frame)
    func_m = re.search(r'func="([^"]+)"', frame)

    lineno = line_m.group(1) if line_m else "?"
    fname = file_m.group(1).split("/")[-1] if file_m else "?"
    func = func_m.group(1) if func_m else "?"

    out = gdb.cmd(f"list {lineno},{lineno}")
    src = ""
    for l in out:
        m = re.search(r'~"\d+\\t\s*(.+)\\n"', l)
        if m:
            src = m.group(1).strip()
            break

    return fname, func, lineno, src


def get_variables(gdb: GDB):
    lines = gdb.cmd("-stack-list-variables --all-values")

    output = " ".join(lines)
    names = re.findall(r'name="(\w+)"', output)
    variables = []
    for name in names:
        addr = parse_addr(" ".join(gdb.cmd(f"print/x &{name}")))
        typ = parse_type(" ".join(gdb.cmd(f"whatis {name}")))
        size = parse_size(" ".join(gdb.cmd(f"print sizeof({name})")))
        variables.append({"name": name, "addr": addr, "type": typ, "size": size})

    return variables


commands = {
    "n": "-exec-next",
    "s": "-exec-step",
    "r": "-exec-continue",
}


def main() -> None:
    p = argparse.ArgumentParser(description="mem visualizer")
    p.add_argument("binary")  # this is for compiled C code using -g
    p.add_argument(
        "--line",
        "-l",
        type=int,
        nargs="+",
        help="Breakpoint lines e.g. --line 10 17 25",
    )
    p.add_argument("--func", "-f", help="Break at function name (default:main)")
    p.add_argument(
        "--input",
        "-i",
        help="Stdin to feed the program, like '3 10 20 30' ",
    )
    args = p.parse_args()

    gdb = GDB(args.binary)

    locs = []
    if args.line:
        locs += [str(l) for l in args.line]
    if args.func:
        locs.append(args.func)
    if not locs:
        locs.append("main")

    for loc in locs:
        gdb.cmd(f"-break-insert {loc}")

    if args.input:
        tf = tempfile.NamedTemporaryFile(mode="w", suffix=".in", delete=False)
        tf.write(args.input)
        tf.flush()
        tf.close()
        gdb.run_cmd(f'-interpreter-exec console "run < {tf.name}"')
        os.unlink(tf.name)
    else:
        gdb.run_cmd("-exec-run")

    gdb.run_cmd("-exec-run")

    snapshot(gdb, get_variables(gdb))

    while True:
        key = read_key()
        if key == "q":
            break
        if key in commands:
            stopped = " ".join(gdb.run_cmd(commands[key]))
            if "exited" in stopped:
                print("\n  program finished")
                break
            variables = get_variables(gdb)
            snapshot(gdb, variables)

    gdb.close()


if __name__ == "__main__":
    main()
