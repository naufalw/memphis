import argparse
import re

from aesthetics import GRN, R, read_key, render_var
from gdb import GDB
from parser_gdb import (
    heap_size,
    is_pointer,
    parse_addr,
    parse_size,
    parse_type,
    read_bytes,
    read_pointer,
)


def snapshot(gdb, variables):
    print("\033[2J\033[H", end="")

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

    print("\n  n=next  q=quit")


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

    snapshot(gdb, get_variables(gdb))

    while True:
        key = read_key()
        if key == "q":
            break
        if key == "n":
            stopped = " ".join(gdb.run_cmd("-exec-next"))
            if "exited" in stopped:
                print("\n  program finished")
                break
            variables = get_variables(gdb)
            snapshot(gdb, variables)

    gdb.close()


if __name__ == "__main__":
    main()
