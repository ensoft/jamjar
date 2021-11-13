# ------------------------------------------------------------------------------
# test_database.py - Database modul tests
#
# November 2015, Phil Connell
# ------------------------------------------------------------------------------

"""Database tests."""

__all__ = ()


import unittest

from .. import database


class DatabaseTest(unittest.TestCase):
    """Tests for the Database class."""

    def setUp(self):
        self._db = database.Database()

    def tearDown(self):
        self._db = None

    def test_get_target(self):
        """Test the get_target method."""
        foo_a = self._db.get_target("foo")
        self.assertEqual(foo_a.name, "foo")
        foo_b = self._db.get_target("foo")
        self.assertIs(foo_a, foo_b)

    def test_repr(self):
        """Test that databases repr correctly."""
        self._db.get_target("foo")
        self._db.get_target("bar")
        self.assertEqual(repr(self._db), "Database(2 targets)")

    def test_find_targets(self):
        """Test the find_targets method."""
        self._db.get_target("foo")
        self._db.get_target("foo1")
        self._db.get_target("foo2")
        self._db.get_target("foo-bar")
        self._db.get_target("<f>bar")

        def check_find(name_regex, expected_names):
            self.assertEqual(
                list(self._db.find_targets(name_regex)),
                [self._db.get_target(name) for name in expected_names],
            )

        check_find("foo", ["foo", "foo1", "foo2", "foo-bar"])
        check_find("foo\d", ["foo1", "foo2"])
        check_find("f.*bar", ["foo-bar", "<f>bar"])


class TargetTest(unittest.TestCase):
    """Tests for the Target class."""

    def setUp(self):
        self.first = database.Target("abc")
        self.second = database.Target("def")
        self.third = database.Target("ghi")

    def tearDown(self):
        self.first = None
        self.second = None
        self.third = None

    def test_repr(self):
        """Test that targets repr correctly."""
        self.assertEqual(repr(self.first), "Target(abc)")

    def test_add_dependency(self):
        """Test the add_dependency method."""
        self.first.add_dependency(self.third)
        self.first.add_dependency(self.second)
        self.third.add_dependency(self.second)

        # Ordering is maintained!
        self._check_deps(self.first, [self.third, self.second])
        self._check_deps(self.second, [])
        self._check_deps(self.third, [self.second])

        self._check_deps_rev(self.first, set())
        self._check_deps_rev(self.second, {self.first, self.third})
        self._check_deps_rev(self.third, {self.first})

    def test_add_inclusion(self):
        """Test the add_inclusion method."""
        self.first.add_inclusion(self.third)
        self.first.add_inclusion(self.second)
        self.third.add_inclusion(self.second)

        # Ordering is maintained!
        self._check_incs(self.first, [self.third, self.second])
        self._check_incs(self.second, [])
        self._check_incs(self.third, [self.second])

        self._check_incs_rev(self.first, set())
        self._check_incs_rev(self.second, {self.first, self.third})
        self._check_incs_rev(self.third, {self.first})

    def test_eq_hash(self):
        """Test target equality and hashing."""
        x = database.Target("foo")
        y = database.Target("foo")
        self.assertIsNot(x, y)
        self.assertEqual(x, y)
        self.assertEqual(hash(x), hash(y))
        z = database.Target("foo!")
        self.assertNotEqual(x, z)
        self.assertNotEqual(hash(x), hash(z))

    def test_filename(self):
        """Test the filename method."""
        tgt = database.Target("<grist nonsense>this_is-the_filename.abc")
        self.assertEqual(tgt.filename(), "this_is-the_filename.abc")

    def test_grist(self):
        """Test the grist method."""
        tgt = database.Target("<grist!nonsense>this_is-the_filename.abc")
        self.assertEqual(tgt.grist(), "<grist!nonsense>")

    def test_brief_name(self):
        """Test the brief name method."""
        tgt = database.Target("<blah!grist!ablah!bblah>some_filename xyz.foo")
        self.assertEqual(
            tgt.brief_name(), "<blah!grist!...>some_filename xyz.foo"
        )

    # --------------------------------------------------------------------------
    # Helpers
    #

    def _check_deps(self, target, expected):
        """Check that the deps attribute of target is as expected."""
        self.assertEqual(list(target.deps), expected)

    def _check_deps_rev(self, target, expected):
        """Check that the deps_rev attribute of target is as expected."""
        self.assertEqual(set(target.deps_rev), expected)

    def _check_incs(self, target, expected):
        """Check that the incs attribute of target is as expected."""
        self.assertEqual(list(target.incs), expected)

    def _check_incs_rev(self, target, expected):
        """Check that the incs_rev attribute of target is as expected."""
        self.assertEqual(set(target.incs_rev), expected)
