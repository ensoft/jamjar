# ------------------------------------------------------------------------------
# query.py - Database query module
#
# November 2015, Phil Connell
# ------------------------------------------------------------------------------

"""Target query functions."""

__all__ = (
    "deps",
    "dep_chains",
    "all_deps_bf",
    "all_deps_df",
)


import collections


def deps(target):
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


def deps_rebuilt(target):
    """
    Iterator that yields immediate rebuilt dependencies of a target.
    """
    for dep in deps(target):
        if dep.rebuilt:
            yield dep


def dep_chains(target, *, max_depth=0, include_target=None):
    """
    Iterator that yields dependency chains for a target.

    In each list:

    - The first target is the given target.
    - The target at index N depends on the target at index N + 1.
    - The final target doesn't depend on anything.

    The order that chains are produced in is arbitrary.

    :param max_depth:
        Terminate all chains at this depth, rather than going as deep as
        possible.

    :param include_target:
        Function to determine whether chains including a particular output may
        be included in this function's output.

        This is passed a target and should return a bool:

        - True indicates that chains involving the target *may* be returned.
        - False indicates that chains involving the target *must not* be
          returned.

    """
    chains = []
    chains.append([target])
    while chains:
        extended_chains = []
        for chain in chains:
            next_deps = list(deps(chain[-1]))
            if not next_deps or (max_depth and len(chain) == max_depth):
                yield chain
            else:
                extended_chains.extend(
                    chain + [dep]
                    for dep in deps(chain[-1])
                    if include_target is None or include_target(dep)
                )
        chains = extended_chains


def dep_chains_rebuilt(target):
    """Iterator that yields dependency chains that have (all) been rebuilt."""
    yield from dep_chains(target, include_target=lambda target: target.rebuilt)


def rebuild_chains(target):
    """
    Return the chains of targets that caused a given target to be rebuilt.
    """
    chains = [_basic_rebuild_chain(target)]
    while True:
        extended_chains = []
        for chain in chains:
            for dep in deps_rebuilt(chain[-1]):
                extended_chains.append(chain + _basic_rebuild_chain(dep))
        if extended_chains:
            chains = extended_chains
        else:
            break
    return chains


def _basic_rebuild_chain(target):
    """
    Get a rebuild chain based purely on 'rebuild info' from Jam.
    """
    chain = [target]
    current = target
    while True:
        current = current.rebuild_info.dep
        if current is None:
            break
        else:
            chain.append(current)
    return chain


def all_deps_bf(target):
    """
    Iterator that yields all dependencies of a target, breadth-first.

    This function may yield the same target more than once.

    """
    queue = collections.deque()
    queue.extend(deps(target))
    while queue:
        current = queue.popleft()
        yield current
        queue.extend(deps(current))


def all_deps_df(target):
    """
    Iterator that yields all dependencies of a target, depth-first.

    This function may yield the same target more than once.

    """
    stack = []
    # Make sure we'll yield dependencies in Jam definition order!
    rev_deps = lambda target: reversed(list(deps(target)))
    stack.extend(rev_deps(target))
    while stack:
        current = stack.pop()
        yield current
        stack.extend(rev_deps(current))
