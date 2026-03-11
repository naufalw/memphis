import argparse
import re
import subprocess


class GDB:
    """
    GDB wrapper hehe.
    """

    def __init__(self, binary: str):
        self.proc = subprocess.Popen(
            ["gdb", "--interpreter=mi2", "--quiet", binary],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )

    def _readline(self) -> str:
        "Read output line from gdb"
        while True:
            line = self.proc.stdout.readline()
            if line:
                return line.strip()

    def _drain(self):
        "Drain unnecessary yap from gdb"
        while True:
            if self._readline().startswith("(gdb)"):
                return

    def cmd(self, c: str) -> list[str]:
        """for commands ends with (gdb)"""
        self.proc.stdin.write(c + "\n")
        self.proc.stdin.flush()
        lines = []
        while True:
            l = self._readline()
            if l.startswith("(gdb)"):
                return lines
            lines.append(l)

    def run_cmd(self, c: str) -> list[str]:
        """for commands ends with *stopped"""
        self.proc.stdin.write(c + "\n")
        self.proc.stdin.flush()
        lines = []
        while True:
            l = self._readline()
            lines.append(l)
            if l.startswith("*stopped"):
                self._drain()
                return lines

    def close(self):
        try:
            self.proc.stdin.write("-gdb-exit\n")
            self.proc.stdin.flush()
        except Exception:
            pass
        self.proc.terminate()


def main() -> None:
    p = argparse.ArgumentParser(description="mem visualizer")
    p.add_argument("binary")  # this is for compiled C code using -g
    p.add_argument("--line", "-l", type=int, help="Breakpoint at source line")
    p.add_argument("--func", "-f", help="Break at function name (default:main)")
    p.add_argument(
        "--input",
        "-i",
        help="Stdin to feed the program, like '3 10 20 30' ",
    )
    args = p.parse_args()

    gdb = GDB(args.binary)

    loc = str(args.line) if args.line else (args.func or "main")

    gdb.cmd(f"-break-insert {loc}")
    gdb.run_cmd("-exec-run")

    lines = gdb.cmd("-stack-list-variables --all-values")

    output = " ".join(lines)
    names = re.findall(r'name="(\w+)"', output)
    variables = []
    for name in names:
        addr = parse_addr(" ".join(gdb.cmd(f"print/x &{name}")))
        typ = parse_type(" ".join(gdb.cmd(f"whatis {name}")))
        size = parse_size(" ".join(gdb.cmd(f"print sizeof({name})")))
        variables.append({"name": name, "addr": addr, "type": typ, "size": size})
        print(f"{name}: addr={addr} type={typ} size={size}")

    gdb.close()


if __name__ == "__main__":
    main()
