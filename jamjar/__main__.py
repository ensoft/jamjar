
# __main__.py - Main module
#
# November 2015, Phil Connell
#------------------------------------------------------------------------------

"""Main entrypoint!"""


import argparse
import sys

from . import database
from . import parsers
from . import ui


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--logfile",
                        help="Path to the jam log file to parse",
                        required=True)
    parser.add_argument("-d", "--parsers",
                        help="Jam debug options to run parsers for",
                        required=False,
                        default="dmc")
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    db = database.Database()
    parsers.parse(db, args.logfile, args.parsers)
    cli_ui = ui.UI(db)
    cli_ui.cmdloop()


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except (KeyboardInterrupt, SystemExit):
        # Exit gracefully.
        pass
    # Uncomment for debugging.
    #except Exception:
    #    import traceback; traceback.print_exc()
    #    import pdb; pdb.post_mortem()

