import argparse


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


if __name__ == "__main__":
    main()
