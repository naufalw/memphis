import re

from gdb import GDB


def parse_addr(raw: str) -> str | None:
    m = re.search(r"\$\d+ = (0x[0-9a-f]+)", raw)
    return m.group(1) if m else None


def parse_type(raw: str) -> str | None:
    m = re.search(r"type = ([^\\]+)", raw)
    return m.group(1).strip() if m else None


def parse_size(raw: str) -> int | None:
    m = re.search(r"\$\d+ = (\d+)", raw)
    return int(m.group(1)) if m else None


def read_bytes(gdb: GDB, addr, size) -> list[int]:
    out = " ".join(gdb.cmd(f"-data-read-memory-bytes {addr} {size}"))
    m = re.search(r'contents="([0-9a-f]+)"', out)
    if not m:
        return []
    hex_str = m.group(1)
    return [int(hex_str[i : i + 2], 16) for i in range(0, len(hex_str), 2)]
