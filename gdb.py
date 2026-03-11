import subprocess
from io import TextIOWrapper


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
