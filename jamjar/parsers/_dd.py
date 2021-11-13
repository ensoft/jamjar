# ------------------------------------------------------------------------------
# _dd.py
#
# Parser for the jam 'd' debug flag output - which contains details of
# file dependencies, and inclusions.
#
# November 2015, Jonathan Loh
# ------------------------------------------------------------------------------

"""jam -dd output parser"""

__all__ = ("DDParser",)


import re
from typing import Iterable

from ._base import BaseParser


class DDParser(BaseParser):
    """Parser for '-dd' debug output."""

    def parse(self, logs: Iterable[str]) -> None:
        """Parse '-dd' debug output from the given jam logs."""
        for line in logs:
            self._parse_line(line)

    # One of:
    #   Depends "<grist>file.name" : "<grist>other.name" ;
    #   Includes "<grist>file.name" : "<grist>other.name" ;
    _dependency_regex = re.compile(
        r'\s*(?:Depends|Includes)\s+"(?P<from>[^"]+)"\s+:\s+"(?P<onto>[^"]+)"'
    )

    def _parse_line(self, line: str) -> None:
        """Handle a single line, updating the database if necessary."""
        is_depends = line.startswith("Depends ")
        is_includes = line.startswith("Includes ")
        if is_depends or is_includes:
            match = self._dependency_regex.match(line)
            if match is None:
                raise ValueError(
                    f"Expected to get dependency information from {line!r} "
                    f"but failed to match the expected format"
                )
            from_target = self.db.get_target(match.group("from"))
            onto_target = self.db.get_target(match.group("onto"))
            if is_depends:
                from_target.add_dependency(onto_target)
            else:
                assert is_includes
                from_target.add_inclusion(onto_target)
