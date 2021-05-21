# ------------------------------------------------------------------------------
# test_dc_parser.py - Test for the -dc parser module
#
# November 2015, Zoe Kelly
# ------------------------------------------------------------------------------

"""dc parser tests."""

__all__ = ()


import unittest

from .. import database
from .. import parsers


class DmParserTest(unittest.TestCase):
    """Tests for the jam dm parser"""

    def setUp(self):
        self._db = database.Database()
        self._parser = parsers.DCParser(self._db)

    def tearDown(self):
        self._dc_parser = None
        self._db = None

    def test_timestamp_chain(self):
        """Test parsing of timestamp inheritance chains."""
        lines = []
        lines.append(self._make_outdated("irrelevant", "head"))
        lines.extend(self._make_timestamp_chain("head", "mid_a", "mid_b", "tail"))

        self._parser._parse(lines)
        head = self._db.get_target("head")
        mid_a = self._db.get_target("mid_a")
        mid_b = self._db.get_target("mid_b")
        tail = self._db.get_target("tail")

        self.assertIsNotNone(head.timestamp_chain)
        self.assertEqual(head.timestamp_chain, [mid_a, mid_b, tail])
        for other in head.timestamp_chain:
            self.assertIsNone(other.timestamp_chain)

    def test_timestamp_chain_multiple(self):
        """Test handling of multiple timestamp chains for the same target."""
        lines = []
        lines.append(self._make_outdated("irrelevant", "head"))
        lines.extend(self._make_timestamp_chain("head", "tail"))
        lines.append(self._make_outdated("different", "head"))
        lines.extend(self._make_timestamp_chain("head", "other"))

        self._parser._parse(lines)
        head = self._db.get_target("head")
        tail = self._db.get_target("tail")

        self.assertIsNotNone(head.timestamp_chain)
        self.assertEqual(head.timestamp_chain, [tail])

    # --------------------------------------------------------------------------
    # Helpers
    #

    def _make_outdated(self, rebuilt, reason):
        """Return an OUTDATED fate line for the given targets."""
        return '   Rebuilding "{}": it is older than "{}"'.format(rebuilt, reason)

    def _make_timestamp_chain(self, *targets):
        """Yield timestamp inheritance lines for targets."""
        fmt = '        "{}" inherits timestamp from "{}"'
        for inheriter, inheritee in zip(targets, targets[1:]):
            yield fmt.format(inheriter, inheritee)
