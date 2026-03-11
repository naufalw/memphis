import argparse
import re

from aesthetics import render_var
from gdb import GDB
from parser_gdb import parse_addr, parse_size, parse_type, read_bytes


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
        # print(f"{name}: addr={addr} type={typ} size={size}")

    for var in variables:
        raw = read_bytes(gdb, var["addr"], var["size"])
        render_var(var, raw)

    gdb.close()


if __name__ == "__main__":
    main()
