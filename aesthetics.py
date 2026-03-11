import sys
import termios
import tty

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
