# ------------------------------------------------------------------------------
# query.py - Database query module
#
# November 2015, Phil Connell
# ------------------------------------------------------------------------------

"""Higher-level query functions (vs. raw database reads)."""

__all__ = (
    "Chain",
    "RebuildChain",
    "deps",
    "deps_rebuilt",
    "rebuild_chains",
    "timestamp_inheritance_chain",
)


import collections
from typing import Callable, Iterator, Optional

from . import database


Chain = list[database.Target]

RebuildChain = list[tuple[database.Target, Optional[database.RebuildReason]]]


def deps(target: database.Target) -> Iterator[database.Target]:
    """
    Iterator that yields immediate dependencies of a target.

    This function:

    - Takes account of Jam 'includes' as well as dependencies.
    - Won't yield the same target more than once.

    """
    yield from target.deps
    # If X includes Y, all dependencies of Y are dependencies of X. Also need
    # to remove duplicates.
    seen = set(target.deps)
    inc_deps = (dep for inc in target.incs for dep in inc.deps)
    for dep in inc_deps:
        if dep not in seen:
            seen.add(dep)
            yield dep


def deps_rebuilt(target: database.Target) -> Iterator[database.Target]:
    """
    Iterator that yields immediate rebuilt dependencies of a target.
    """
    for dep in deps(target):
        if dep.rebuilt:
            yield dep


def rebuild_chains(target: database.Target) -> list[RebuildChain]:
    """
    Return the chains of targets that caused a given target to be rebuilt.
    """
    chains: list[RebuildChain] = [_basic_rebuild_chain(target)]
    while True:
        extended_chains = []
        for chain in chains:
            for dep in deps_rebuilt(chain[-1][0]):
                extended_chains.append(chain + _basic_rebuild_chain(dep))
        if extended_chains:
            chains = extended_chains
        else:
            break
    return chains


def _basic_rebuild_chain(target: database.Target) -> RebuildChain:
    """
    Get a rebuild chain based purely on 'rebuild info' from Jam.
    """
    chain: RebuildChain = [(target, None)]
    current: Optional[database.Target] = target
    assert current is not None
    while True:
        reason = current.rebuild_reason
        current = current.rebuild_reason_target
        if current is None:
            break
        else:
            chain.append((current, reason))
    return chain


def timestamp_inheritance_chain(target: database.Target) -> Optional[Chain]:
    """
    Return the chain of targets that this target inherits its timestamp from.
    """
    if target.inherits_timestamp_from is None:
        return None

    chain: Chain = []
    current: Optional[database.Target] = target
    while current is not None:
        chain.append(current)
        current = current.inherits_timestamp_from
    return chain
