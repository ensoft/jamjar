# ------------------------------------------------------------------------------
# __init__.py - Parsers package root
#
# December 2015, Antony Wallace
# ------------------------------------------------------------------------------

"""Parsers for Jam debug output."""

__all__ = ("parse", "DDParser", "DMParser", "DCParser")

import pathlib

from .. import database

from ._dd import DDParser
from ._dm import DMParser
from ._dc import DCParser


def parse(db: database.Database, logfile: pathlib.Path) -> None:
    """
    Parse as much information as possible from the given log file into a DB.

    :param db:
        Target database to populate.
    :param logfile:
        Source jam log file containing debug output.

    """
    for parser_cls in [DCParser, DDParser, DMParser]:
        print("Running {}".format(parser_cls.__name__))
        with open(logfile) as logs:
            parser_cls(db).parse(logs)
