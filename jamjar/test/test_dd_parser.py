# ------------------------------------------------------------------------------
# test_dd_parser.py - Test for the -dd parser module
#
# November 2015, Jonathan Loh
# ------------------------------------------------------------------------------

"""dd parser tests tests."""

__all__ = ()


import os.path
import unittest

from .. import database
from .. import parsers


class DdParserTest(unittest.TestCase):
    """Tests for the jam dd parser"""

    def setUp(self):
        self._db = database.Database()
        self._dd_parser = parsers.DDParser(self._db)
        self._logdir = os.path.join(os.path.dirname(__file__), "example_log")

    def tearDown(self):
        self._db = None

    def test_parse_file(self):
        """Test the file parsing."""
        self._dd_parser.parse_logfile(os.path.join(self._logdir, "example_dd.log"))

        # Check the expected targets are in the db
        targets = list(self._db.find_targets("p"))
        self.assertEqual(len(targets), 1)
        self.assertEqual(len(targets[0].deps), 3)
        self.assertEqual(targets[0].deps[0].name, "q")
        self.assertEqual(targets[0].deps[1].name, "s")
        self.assertEqual(targets[0].deps[2].name, "t")

        targets = list(self._db.find_targets("a"))

        self.assertEqual(len(targets[0].incs), 1)
        self.assertEqual(targets[0].incs[0].name, "b")
