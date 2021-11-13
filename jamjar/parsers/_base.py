# ------------------------------------------------------------------------------
# base_parser.py
#
# Base class specifying the API for Jam debug parsers to implement.
#
# November 2015, Antony Wallace
# ------------------------------------------------------------------------------

"""Jam debug parser base class."""

__all__ = ("BaseParser",)

from typing import Iterable

from .. import database


class BaseParser:
    """
    Base class for a parser of jam debug output.

    .. attribute:: db

        Database to be updated with parsed debug information.

    """

    def __init__(self, db: database.Database) -> None:
        self.db = db

    def parse(self, logs: Iterable[str]) -> None:
        """Update the database based on parsing the given jam log file."""
        raise NotImplementedError
