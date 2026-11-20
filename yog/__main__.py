"""python -m yog <command>

  update   re-download changed wiki pages -> parse -> translate (new strings only) -> number check
           -> tests -> site build; writes data/CHANGELOG.md. See `python -m yog update --help`.
"""
from __future__ import annotations

import sys

from . import update


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0 if argv else 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "update":
        return update.main(rest)
    print(f"unknown command {cmd!r}\n\n{__doc__.strip()}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
