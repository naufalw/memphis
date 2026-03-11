GRN = "\033[92m"
CYN = "\033[96m"
YEL = "\033[93m"
DIM = "\033[2m"
R = "\033[0m"


def fmt_byte(b: int, char_mode: bool = False) -> str:
    if b == 0:
        return f"{DIM} \\0{R}"
    if 32 <= b <= 126:
        if char_mode:
            return f"{GRN}'{chr(b)}'{R}"
        return f"{CYN}{b:3d}{R}"
    return f"{YEL}{b:3d}{R}"


def render_var(var, raw):
    name = var["name"]
    typ = var["type"]
    size = var["size"]
    is_char = "char" in typ

    print(f"\n  {name}  {typ}  ({size} bytes)")

    max_cols = 8
    separator = f" {DIM}│{R} "
    rows = [raw[i : i + max_cols] for i in range(0, len(raw), max_cols)]
    base = int(var["addr"], 16)

    for ri, row in enumerate(rows):
        row_addr = hex(base + ri * max_cols)
        cells = separator.join(fmt_byte(b, is_char) for b in row)
        print(f"  {row_addr} │ {cells} │")

        # 2 (indent) + len(address) + 3 (" │ ") = start of first cell
        pad = " " * (2 + len(row_addr) + 3)
        ruler = "".join(f"{('+' + str(i)).center(3)}   " for i in range(len(row)))
        print(f"{pad}{ruler}")
