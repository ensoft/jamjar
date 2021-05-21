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


from ._base import BaseParser


class DCParser(BaseParser):
    """Parser for '-dc' debug output."""

    # Are a series of 'inherits timestamp' lines expected next?
    _timestamp_chain_follows = False
    # Target that owns the following timestamp chain.
    _timestamp_chain_owner = None

    def parse_logfile(self, filename):
        """Parse '-dc' debug output from the file at the given path."""
        with open(filename, errors="ignore") as f:
            self._parse(f)

    def _parse(self, lines):
        """
        Parse debug from an iterable of lines.

        This is separated out from parse_logfile for testing purposes.

        """
        # Make sure we have an iterator so it can be advanced manually when
        # required.
        lines = iter(lines)
        for line in lines:
            # Are there a series of timestamp lines to parse?
            if self._timestamp_chain_follows:
                while line.split(maxsplit=1)[1].startswith("inherits timestamp from"):
                    self._parse_timestamp_line(line)
                    try:
                        line = next(lines)
                    except StopIteration:
                        break
                self._timestamp_chain_follows = False
                self._timestamp_chain_owner = None

            line = line.strip()
            if line.startswith("Rebuilding"):
                self._parse_rebuilding_line(line)

    def _strip_quoted_target(self, word):
        """Strip quotes from a target name."""
        if word[-1] == ":":
            word = word[:-1]
        assert word[0] == word[-1] == '"'
        return word[1:-1]

    def _target_from_quoted_name(self, word):
        """Obtain a target object from a quoted name."""
        name = self._strip_quoted_target(word)
        return self.db.get_target(name)

    def _expect_timestamp_chain(self, target):
        """Set up state for handling a timestamp chain on target next."""
        # Only parse the first chain for any given target.
        if target.timestamp_chain is None:
            target.timestamp_chain = []
            self._timestamp_chain_follows = True
            self._timestamp_chain_owner = target

    def _parse_rebuilding_line(self, line):
        """Parse a 'Rebuilding "<target>" ...' line."""
        words = line.split()
        assert words[0] == "Rebuilding"

        rebuilt_target = self._target_from_quoted_name(words[1])
        rebuilt_target.set_rebuilt()

        # First two words of the reason is enough to determine the target's
        # fate.
        reason_start = words[2:4]
        if reason_start == ["it", "is"]:  # ... older than <tgt>
            # OUTDATED
            assert words[4:6] == ["older", "than"]
            reason_target = self._target_from_quoted_name(words[6])
            rebuilt_target.set_rebuilt_dep(reason_target)
            self._expect_timestamp_chain(reason_target)
        elif reason_start[0] == "dependency":  # ... <tgt> was updated
            # UPDATE
            assert words[4:6] == ["was", "updated"]
            reason_target = self._target_from_quoted_name(words[3])
            rebuilt_target.set_rebuilt_dep(reason_target)
        elif reason_start == ["it", "was"]:  # ... mentioned with '-t'
            # TOUCHED
            pass
        elif reason_start == ["it", "doesn't"]:  # ... exist
            # MISSING
            pass
        elif reason_start == ["it", "depends"]:  # ... on newer <tgt>
            # NEEDTMP
            assert words[4:6] == ["on", "newer"]
            reason_target = self._target_from_quoted_name(words[6])
            rebuilt_target.set_rebuilt_dep(reason_target)
            self._expect_timestamp_chain(reason_target)

    def _parse_timestamp_line(self, line):
        """Parse a '<target> inherits timestamp from ...' line."""
        words = line.split()
        assert words[1:4] == ["inherits", "timestamp", "from"]

        chain = self._timestamp_chain_owner.timestamp_chain
        parent_target = self._target_from_quoted_name(words[0])
        child_target = self._target_from_quoted_name(words[4])
        assert not chain or parent_target is chain[-1]
        chain.append(child_target)
