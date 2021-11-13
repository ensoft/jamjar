# ------------------------------------------------------------------------------
# _dm.py
#
# Parser for the jam 'm' debug flag output - which contains details of
# timestamps, whether or not a file was updated, and gristed targets to file
# bindings.
#
# November 2015, Antony Wallace
# ------------------------------------------------------------------------------

"""jam -dm output parser"""

__all__ = ("DMParser",)

import datetime
import re
from typing import Iterable

from .. import database
from ._base import BaseParser


class DMParser(BaseParser):
    """Parser for '-dm' debug output."""

    def parse(self, logs: Iterable[str]) -> None:
        """Parse '-dm' debug output from the given jam logs."""
        for line in logs:
            self._parse_line(line)

    _time_re = re.compile(r"time\s+--\s+(?P<target>.+):\s+(?P<info>.+)")
    _bind_re = re.compile(r"bind\s+--\s+(?P<target>.+):\s+(?P<path>.+)")
    _made_re = re.compile(r"made[+*]?\s+(?P<fate>[a-z]+)\s+(?P<target>.+)")

    def _parse_line(self, line: str) -> None:
        """Parse a single line, updating the database as necessary."""
        # The output we are interested in takes one of the following forms:
        # make -- <target>
        # time -- <target>:timestamp
        # made [stable|update] <target>
        # bind -- <target>:filename
        #
        # Call the parse functions for each of these in turn (apart from the
        # 'make' line which is entirely uninteresting). Stop on the first
        # parser that manages to parse any information.
        for parser in [
            self._parse_time_line,
            self._parse_made_line,
            self._parse_bind_line,
        ]:
            if parser(line):
                break

    def _parse_time_line(self, line: str) -> bool:
        """Attempt to parse a 'time ...' line."""
        if "time" not in line or (m := self._time_re.match(line)) is None:
            return False

        target = self.db.get_target(m.group("target"))
        # See `target_bind` in jam. A timestamp is output only for "exists"
        # and not the other binding states.
        if m.group("info") not in {"missing", "unbound", "parents"}:
            dt = datetime.datetime.strptime(
                m.group("info"), "%a %b %d %H:%M:%S %Y"
            )
            target.set_timestamp(dt)
        return True

    def _parse_bind_line(self, line: str) -> bool:
        """Attempt to parse a 'bind ...' line."""
        if "bind" not in line or (m := self._bind_re.match(line)) is None:
            return False

        target = self.db.get_target(m.group("target"))
        target.set_binding(m.group("path"))
        return True

    def _parse_made_line(self, line: str) -> bool:
        """Attempt to parse a 'made ...' line."""
        if "made" not in line or (m := self._made_re.match(line)) is None:
            return False

        target = self.db.get_target(m.group("target"))
        fate = database.Fate(m.group("fate"))
        target.set_fate(fate)
        return True
