# ------------------------------------------------------------------------------
# _dc.py
#
# Parser for the jam 'c' debug flag output - which contains the names of files
# that cause rebuilds - ie new sources, missing targets
#
# November 2015, Zoe Kelly
# ------------------------------------------------------------------------------

"""jam -dc output parser"""

__all__ = ("DCParser",)

import collections
import re
from typing import Iterable, Iterator, Optional

from .. import database

from ._base import BaseParser


class DCParser(BaseParser):
    """Parser for '-dc' debug output."""

    # See DEBUG_CAUSES in jam for the relevant debug output.

    def parse(self, logs: Iterable[str]) -> None:
        """Parse '-dc' debug output from the given jam logs."""
        lines = collections.deque(logs)
        while True:
            line = self._consume_line(lines)
            if line is None:
                break

            target = self._parse_fate_line(line)
            if target is not None:
                line = self._consume_line(lines)
                if line is None:
                    break

                older_target = self._parse_newer_than_line(line)
                if older_target is not None:
                    # Record the info and go back to the top; we've consumed
                    # all of the inter-related lines.
                    target.add_i_am_newer_than(older_target)
                    continue

            # Two possibilities at this point:
            #   - Still processing the first line from this iteration; it was
            #     not fate-related
            #   - First line did give fate information, but the second line
            #     wasn't giving related "newer than" information.
            #
            # Either way we're now on to some form of "rebuilding" line, or a
            # line that's not interesting at all.
            rebuilding = self._parse_rebuilding_line(line)

            # May have some timestamp inheritance info to follow.
            if rebuilding:
                self._parse_inherits_timestamp_lines(lines)

    def _consume_line(self, lines: collections.deque[str]) -> Optional[str]:
        """
        Read the next line.

        - Returns `None` if there's no remaining input.
        - Otherwise returns the next line with whitespace stripped at the start
          and end.

        """
        try:
            line = lines.popleft()
        except IndexError:
            return None
        else:
            return line.strip()

    def _regurgitate_line(
        self, lines: collections.deque[str], line: str
    ) -> None:
        """
        Express regret for eating a line,

        Makes it available for the next `_consume_line` call.

        """
        lines.appendleft(line)

    _causes_fates = {
        database.Fate.NEWER.value,
        database.Fate.TEMP.value,
        database.Fate.TOUCHED.value,
        database.Fate.MISSING.value,
    }

    def _is_fate(self, line: str) -> bool:
        """Does the given line report a target's fate?"""
        return any(
            line.startswith(fate_name) for fate_name in self._causes_fates
        )

    def _parse_fate_line(self, line: str) -> Optional[database.Target]:
        """
        Attempt to parse a target's fate.

        Returns `None` if this wasn't a fate line, or the target whose fate was
        set otherwise.

        """
        if not self._is_fate(line):
            return None
        else:
            fate_name, target_name = line.split(maxsplit=1)
            target = self.db.get_target(target_name)
            fate = database.Fate(fate_name)
            target.set_fate(fate)
            return target

    def _parse_newer_than_line(self, line: str) -> Optional[database.Target]:
        """
        Attempt to parse "newer than" information.

        Returns `None` if this wasn't a "newer than" line, or the *older*
        target otherwise.

        """
        if not line.startswith("newer than:"):
            return None
        else:
            older_target_name = line.split(":", maxsplit=1)[1].strip()
            return self.db.get_target(older_target_name)

    _rebuilding_target_regex = re.compile(r'[^"]+\s+"(?P<target>[^"]+)"')
    _rebuilding_reason_regex = re.compile(
        r'(?P<reason>[^"]+)\s+"(?P<target>[^"]+)"'
    )

    def _parse_rebuilding_line(self, line: str) -> bool:
        """
        Attempt to parse "rebuilding" information.

        Update the database with any interesting information found.

        Return `True` if anything was parsed.

        """
        if not (
            line.startswith("Rebuilding ")
            or line.startswith("Inclusions rebuilding for ")
        ):
            return False

        else:
            # e.g.
            #
            # Rebuilding "<foo>bar.h": it is older than "<baz>quux.h"
            # Rebuilding "<foo>bar.h": inclusion of dependency "<baz>quux.h" was updated
            # Rebuilding "<foo>bar.h": build action was updated
            target_info, reason_info = line.split(":", maxsplit=1)
            match = self._rebuilding_target_regex.match(target_info)
            if match is None:
                raise ValueError(f"Couldn't parse target from {target_info=}")
            target = self.db.get_target(match.group("target"))

            reason_info = reason_info.strip()
            # Don't need any trailing 'was updated' to disambiguate.
            reason_info = reason_info.removesuffix("was updated").strip()

            reason: str
            related_target: Optional[database.Target]
            match = self._rebuilding_reason_regex.match(reason_info)
            if match is not None:
                reason = match.group("reason")
                related_target = self.db.get_target(match.group("target"))
            else:
                reason = reason_info
                related_target = None

            if reason == "it was mentioned with '-t'":
                target.set_rebuild_reason(database.RebuildReason.TOUCHED)
            elif reason == "build action":
                target.set_rebuild_reason(database.RebuildReason.ACTION)
            elif reason == "it doesn't exist":
                target.set_rebuild_reason(database.RebuildReason.MISSING)
            elif reason == "it depends on newer":
                target.set_rebuild_reason(
                    database.RebuildReason.NEEDTMP, related_target
                )
            elif reason == "it is older than":
                target.set_rebuild_reason(
                    database.RebuildReason.OUTDATED, related_target
                )
            elif reason == "inclusion of inclusion":  # ...was updated
                target.set_rebuild_reason(
                    database.RebuildReason.UPDATED_INCLUDE_OF_INCLUDE,
                    related_target,
                )
            elif reason == "inclusion of dependency":  # ...was updated
                target.set_rebuild_reason(
                    database.RebuildReason.UPDATED_INCLUDE_OF_DEPENDENCY,
                    related_target,
                )
            elif reason == "inclusion":  # ...was updated
                target.set_rebuild_reason(
                    database.RebuildReason.UPDATED_INCLUDE, related_target
                )
            elif reason == "dependency":  # ...was updated
                target.set_rebuild_reason(
                    database.RebuildReason.UPDATED_DEPENDENCY, related_target
                )
            else:
                raise NotImplementedError(
                    f"{reason=}, {target=}, {related_target=}"
                )

            return True

    _inherits_timestamp_regex = re.compile(
        r'"(?P<target>[^"]+)"\s+inherits timestamp from\s+"(?P<source>[^"]+)"'
    )

    def _parse_inherits_timestamp_lines(
        self, lines: collections.deque[str]
    ) -> None:
        """
        Parse a series of timestamp inheritance lines.

        *Only* timestamp inheritance lines are consumed. Any other line is left
        to be consumed by the next `_consume_line` call.

        """
        while True:
            line = self._consume_line(lines)
            if line is None:
                return

            m = self._inherits_timestamp_regex.search(line)
            if m is None:
                self._regurgitate_line(lines, line)
                return

            target = self.db.get_target(m.group("target"))
            source = self.db.get_target(m.group("source"))
            target.set_inherits_timestamp_from(source)
