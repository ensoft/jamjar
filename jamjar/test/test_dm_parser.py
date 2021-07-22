# ------------------------------------------------------------------------------
# test_dm_parser.py - Test for the -dm parser module
#
# November 2015, Antony Wallace
# ------------------------------------------------------------------------------

"""dm parser tests tests."""

__all__ = ()


import unittest

from .. import database
from .. import parsers


class DmParserTest(unittest.TestCase):
    """Tests for the jam dm parser"""

    def setUp(self):
        self._db = database.Database()
        self._dm_parser = parsers.DMParser(self._db)

    def tearDown(self):
        self._db = None

    def test_parse_file(self):
        """Test the file parsing."""
        # @@@!
        # foo_a = self._dm_parser.parse_logfile(...)

        ## Check the expected targets are in the db
        # targets = list(self._db.find_targets(...))
        # self.assertEqual(len(targets), 1)
        # target = database.Target(targets.pop().name)
        # self.assertEqual(target.name, ...)
