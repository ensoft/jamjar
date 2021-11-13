# ------------------------------------------------------------------------------
# database.py - Database module
#
# November 2015, Phil Connell
# ------------------------------------------------------------------------------

"""Target database."""

from __future__ import annotations

__all__ = ("Database", "Fate", "Target", "Rule", "RuleCall")


import collections
import datetime
import enum
import re

from typing import Any, Iterator, Optional, Union


class Fate(enum.Enum):
    """All possible target fates in jam."""

    INIT = "init"
    MAKING = "making"
    STABLE = "stable"
    NEWER = "newer"
    TEMP = "temp"
    TOUCHED = "touched"
    MISSING = "missing"
    NEEDTMP = "needtmp"
    OLD = "old"
    UPDATE = "update"
    NOFIND = "nofind"
    NOMAKE = "nomake"


class RebuildReason(enum.Enum):
    """All possible target fates in jam."""

    TOUCHED = "mentioned with '-t'"
    ACTION = "build action was updated"
    MISSING = "it doesn't exist"
    NEEDTMP = "it depends on newer"
    OUTDATED = "it is older than"
    UPDATED_INCLUDE_OF_INCLUDE = "inclusion of inclusion was updated"
    UPDATED_INCLUDE_OF_DEPENDENCY = "inclusion of dependency was updated"
    UPDATED_INCLUDE = "inclusion was updated"
    UPDATED_DEPENDENCY = "dependency was updated"


class Database:
    """Database of jam targets."""

    def __init__(self) -> None:
        self._targets: dict[str, Target] = collections.OrderedDict()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({len(self._targets)} targets)"

    def get_target(self, name: str) -> Target:
        """Get a target with a given name, creating it if necessary."""
        try:
            target = self._targets[name]
        except KeyError:
            target = Target(name)
            self._targets[name] = target
        return target

    def find_targets(self, name_regex: str) -> Iterator[Target]:
        """Yield all targets whose name matches a regex."""
        for name, target in self._targets.items():
            try:
                if re.search(name_regex, name):
                    yield target
            except re.error as e:
                raise ValueError(str(e))

    def find_rebuilt_targets(self, name_regex: str) -> Iterator[Target]:
        """Yield all rebuilt targets whose name matches a regex."""
        for target in self.find_targets(name_regex):
            if target.rebuilt:
                yield target


class Target:
    """
    Representation of a jam target.

    .. attribute:: name

        Name of the target (including any grist).

    .. attribute:: deps

        Sequence of targets that this target depends on, in the order that the
        dependencies are reported by Jam.

    .. attributes:: deps_rev

        Set of targets that depend on this target.

    .. attribute:: incs

        Sequence of targets that this target includes (in the Jam sense!) in
        the order that the inclusions are reported by Jam.

    .. attribute:: incs_rev

        Set of targets that include this target.

    .. attribute:: newer_than

        Sequence of targets that this target is determined to be newer than
        (re. rebuild reasons).

    .. attribute:: older_than

        Set of targets that are older than this target.

    .. attribute:: timestamp

        Timestamp calculated by Jam for this target.

    .. attribute:: inherits_timestamp_from

        Target that gave this target its timestamp (if any).

    .. attribute:: bequeaths_timestamp_to

        Set of targets given the timestamp of this target.

    .. attribute:: binding

        Filesystem path for this target.

    .. attribute:: fate

        Fate of this target in the build.

    .. attribute:: rebuild_reason

        Why this target was rebuilt (or `None` if it wasn't).

    .. attribute:: rebuild_reason_target

        Related target, if applicable for the reason.

    """

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.deps: list[Target] = []
        self.deps_rev: set[Target] = set()
        self.incs: list[Target] = []
        self.incs_rev: set[Target] = set()
        self.newer_than: list[Target] = []
        self.older_than: set[Target] = set()
        self.timestamp: Optional[datetime.datetime] = None
        self.inherits_timestamp_from: Optional[Target] = None
        self.bequeaths_timestamp_to: set[Target] = set()
        self.binding: Optional[str] = None
        self.fate: Optional[Fate] = None
        self.rebuild_reason: Optional[RebuildReason] = None
        self.rebuild_reason_target: Optional[Target] = None

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.name})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def add_dependency(self, other: Target) -> None:
        """Record the target 'other' as depended on by this target."""
        if self not in other.deps_rev:
            self.deps.append(other)
            other.deps_rev.add(self)

    def add_inclusion(self, other: Target) -> None:
        """Record the target 'other' as included by this target."""
        if self not in other.incs_rev:
            self.incs.append(other)
            other.incs_rev.add(self)

    def add_i_am_newer_than(self, older: Target) -> None:
        """Record that this target is newer than the target 'older'."""
        if self not in older.older_than:
            self.newer_than.append(older)
            older.older_than.add(self)

    def brief_name(self) -> str:
        """Return a summarised version of this target's name."""
        # For now, just strip out most of the grist.
        grist, filename = self._grist_and_filename()
        if grist.count("!") > 1:
            brief_grist = "{}!{}!...>".format(
                *grist.split("!", maxsplit=2)[:2]
            )
        else:
            brief_grist = grist
        return brief_grist + filename

    def filename(self) -> str:
        """Return the file name for this target (i.e. strip off gristing)."""
        return self._grist_and_filename()[1]

    def grist(self) -> str:
        """Return this target's grist."""
        return self._grist_and_filename()[0]

    @property
    def rebuilt(self) -> bool:
        """`True` if this target was rebuilt, `False` otherwise."""
        return self.rebuild_reason is not None

    def _grist_and_filename(self) -> tuple[str, str]:
        """Split this target's name into a grist and filename."""
        if self.name.startswith("<"):
            grist, filename = self.name.split(">", maxsplit=1)
            return grist + ">", filename
        else:
            return "", self.name

    def set_timestamp(self, timestamp: datetime.datetime) -> None:
        """Set the updated timestamp on this target."""
        self.timestamp = timestamp

    def set_binding(self, binding: str) -> None:
        """Set the file binding for this target"""
        self.binding = binding

    def set_fate(self, fate: Fate) -> None:
        """Set the fate of this target"""
        # Might end up overwriting an old value if the given log contains debug
        # from a couple of related runs of jam (e.g. in a multiphase build). So
        # don't check...
        self.fate = fate

    def set_rebuild_reason(
        self, reason: RebuildReason, related_target: Optional[Target] = None
    ) -> None:
        """Set the rebuild reason for this target."""
        self.rebuild_reason = reason
        self.rebuild_reason_target = related_target

    def set_inherits_timestamp_from(self, source: Target) -> None:
        """Record that this target inherits its timestamp from another."""
        assert (
            self.inherits_timestamp_from is None
            or self.inherits_timestamp_from == source
        )
        self.inherits_timestamp_from = source
        source.bequeaths_timestamp_to.add(self)
