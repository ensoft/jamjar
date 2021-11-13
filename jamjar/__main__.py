# __main__.py - Main module
#
# November 2015, Phil Connell
# ------------------------------------------------------------------------------

"""Main entrypoint!"""


import argparse
import pathlib
import sys

from . import database
from . import parsers
from . import ui


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--logfile",
        help="Path to the jam log file to parse",
        required=True,
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> None:
    args = parse_args(argv)
    db = database.Database()
    parsers.parse(db, pathlib.Path(args.logfile))
    cli_ui = ui.UI(db)
    cli_ui.cmdloop()


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except (KeyboardInterrupt, SystemExit):
        # Exit gracefully.
        pass
    # Uncomment for debugging.
    # except Exception:
    #    import traceback; traceback.print_exc()
    #    import pdb; pdb.post_mortem()
