# ------------------------------------------------------------------------------
# test_query.py - Query module tests
#
# November 2015, Phil Connell
# ------------------------------------------------------------------------------

"""Database query tests."""

__all__ = ()


import collections
import unittest

from .. import database
from .. import query


class DependencyTest(unittest.TestCase):
    """Test queries related to the dependency graph."""

    _deps = {
        "a": ["b", "c"],
        "b": ["d", "e"],
        "c": ["e"],
        "d": ["f"],
        "e": ["f"],
        "p": ["q"],
        "q": ["r"],
        "x": ["y", "z"],
        # Set up a dep between groups to test filtering of duplicates in the
        # deps() function.
        "y": ["d"],
    }

    # N.B. the chain of deps/incs y -> q -> r -> c, so the 'x' hierarchy of
    # targets has two incs into the 'a' hierarchy (that chain and z -> b).
    _incs = {"y": ["q", "b"], "z": ["b"], "r": ["c"]}

    def setUp(self):
        self._db = database.Database()
        self._targets = collections.OrderedDict()

        for name, deps in self._deps.items():
            target = self._get_target(name)
            for dep in deps:
                dep_target = self._get_target(dep)
                target.add_dependency(dep_target)
        for name, incs in self._incs.items():
            target = self._get_target(name)
            for inc in incs:
                inc_target = self._get_target(inc)
                target.add_inclusion(inc_target)

    def tearDown(self):
        self._db = None
        self._targets = None

    def test_deps(self):
        """Test basic functionality of the deps function."""
        deps = query.deps(self._targets["a"])
        self._check_result(deps, ["b", "c"])

    def test_deps_with_incs(self):
        """Test handling of inclusions by the deps function."""
        deps = query.deps(self._targets["z"])
        self._check_result(deps, ["d", "e"])

    def test_deps_with_both(self):
        """Test handling of both deps and incs by the deps function."""
        deps = query.deps(self._targets["y"])
        # Deps before incs. N.B. that d is both a dep and inc, but the
        # duplicate is filtered out.
        self._check_result(deps, ["d", "r", "e"])

    def test_all_deps_bf(self):
        """Test the breadth-first all_deps function."""
        deps = query.all_deps_bf(self._targets["x"])
        self._check_result(
            deps,
            [
                # x
                "y",
                "z",
                # x.y
                "d",
                "r",
                "e",
                # x.z
                "d",
                "e",
                # x.y.d
                "f",
                # x.y.r
                "e",
                # x.y.e
                "f",
                # x.z.d
                "f",
                # x.z.e
                "f",
                # x.y.d.f
                # x.y.r.e
                "f",
                # x.y.e.f
                # x.z.d.f
                # x.z.e.f
            ],
        )

    def test_all_deps_df(self):
        """Test the depth-first all_deps function."""
        deps = query.all_deps_df(self._targets["x"])
        self._check_result(
            deps,
            [
                "y",
                "d",
                "f",
                "r",
                "e",
                "f",
                "e",
                "f",
                "z",
                "d",
                "f",
                "e",
                "f",
            ],
        )

    def test_dep_chains_basic(self):
        """Test the dep_chains function for one chain.""",
        chains = query.dep_chains(self._targets["c"])
        self._check_chains_result(
            chains,
            [
                ["c", "e", "f"],
            ],
        )

    def test_dep_chains_deeper(self):
        """Test the dep_chains function for multiple chains."""
        chains = query.dep_chains(self._targets["x"])
        self._check_chains_result(
            chains,
            [
                ["x", "y", "d", "f"],
                ["x", "y", "r", "e", "f"],
                ["x", "y", "e", "f"],
                ["x", "z", "d", "f"],
                ["x", "z", "e", "f"],
            ],
        )

    def test_dep_chains_max_depth(self):
        """Test the max_depth parameter of dep_chains."""
        chains = query.dep_chains(self._targets["x"], max_depth=3)
        self._check_chains_result(
            chains,
            [
                ["x", "y", "d"],
                ["x", "y", "r"],
                ["x", "y", "e"],
                ["x", "z", "d"],
                ["x", "z", "e"],
            ],
        )

        chains = query.dep_chains(self._targets["x"], max_depth=2)
        self._check_chains_result(
            chains,
            [
                ["x", "y"],
                ["x", "z"],
            ],
        )

    # --------------------------------------------------------------------------
    # Helpers
    #

    def _check_result(self, got_targets, expected_names):
        """Check that a sequence of targets has the expected names."""
        expected_targets = [
            self._db.get_target(name) for name in expected_names
        ]
        self.assertEqual(list(got_targets), expected_targets)

    def _check_chains_result(self, got_chains, expected_name_chains):
        """
        Check that a sequence of chains of targets have the expected names.
        """
        # Order is currently MIB-lexi. This is a side-effect of the algorithm
        # rather than intentional, so compare as sets!
        expected_chains = {
            tuple(self._db.get_target(name) for name in name_chain)
            for name_chain in expected_name_chains
        }
        got_chains = {tuple(chain) for chain in got_chains}
        self.assertEqual(got_chains, expected_chains)

    def _get_target(self, name):
        """Get a target, ensuring it's stored in the _targets attribute."""
        if name not in self._targets:
            self._targets[name] = self._db.get_target(name)
        return self._targets[name]
