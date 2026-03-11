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
    out = " ".join(gdb.cmd(f"print malloc_usable_size((void*){addr})"))
    m = re.search(r"\$\d+ = (\d+)", out)
    size = int(m.group(1)) if m else 0
    return size if size > 0 else None
