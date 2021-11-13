# ------------------------------------------------------------------------------
# test_query.py - Query module tests
#
# November 2015, Phil Connell
# ------------------------------------------------------------------------------

"""Database query tests."""

__all__ = ()


import pytest

from .. import database
from .. import query


@pytest.fixture
def deps_db() -> database.Database:
    """Database with helpful contents for testing dependency handling."""
    tgt_deps = {
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
    tgt_incs = {"y": ["q", "b"], "z": ["b"], "r": ["c"]}

    db = database.Database()

    for name, deps in tgt_deps.items():
        target = db.get_target(name)
        for dep in deps:
            dep_target = db.get_target(dep)
            target.add_dependency(dep_target)
    for name, incs in tgt_incs.items():
        target = db.get_target(name)
        for inc in incs:
            inc_target = db.get_target(inc)
            target.add_inclusion(inc_target)

    return db


@pytest.mark.parametrize(
    "target,expected_deps",
    [
        # With dependencies.
        ("a", ["b", "c"]),
        # With inclusions.
        ("z", ["d", "e"]),
        # With both.
        ("y", ["d", "r", "e"]),
    ],
)
def test_deps(
    target: str, expected_deps: list[str], deps_db: database.Database
) -> None:
    """Test the deps function."""
    found = list(query.deps(deps_db.get_target(target)))
    expected = list(
        deps_db.get_target(expected_dep) for expected_dep in expected_deps
    )
    assert found == expected
