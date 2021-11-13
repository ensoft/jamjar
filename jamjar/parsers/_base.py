# ------------------------------------------------------------------------------
# base_parser.py
#
# Base class specifying the API for Jam debug parsers to implement.
#
# November 2015, Antony Wallace
# ------------------------------------------------------------------------------

"""Jam debug parser base class."""

__all__ = ("BaseParser",)


class BaseParser:
    """
    Base class for a parser of jam debug output.

    .. attribute:: db

        Database to be updated with parsed debug information.

    """

    def __init__(self, db):
        self.db = db

    def parse_logfile(self, filename):
        """Parse the supplied Jam log file, updating the contents of db with
        the parsed information"""
