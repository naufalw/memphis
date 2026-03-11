import re


def parse_addr(raw: str) -> str | None:
    m = re.search(r"\$\d+ = (0x[0-9a-f]+)", raw)
    return m.group(1) if m else None


def parse_type(raw: str) -> str | None:
    m = re.search(r"type = ([^\\]+)", raw)
    return m.group(1).strip() if m else None


def parse_size(raw: str) -> int | None:
    m = re.search(r"\$\d+ = (\d+)", raw)
    return int(m.group(1)) if m else None
