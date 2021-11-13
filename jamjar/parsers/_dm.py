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

import re
import logging
import time
from datetime import datetime

from .. import database
from ._base import BaseParser


class DMParser(BaseParser):
    """
    Parse the jam 'm' debug flag output from a logfile into the DB supplied at
    initialisation.

    .. attribute:: name

        Name of this parser.

    """

    _made_re = re.compile("made[+*]?\s+([a-z]+)\s+(.+)")
    _time_re = re.compile("time\s+--\s+(.+):\s+(.+)")
    _bind_re = re.compile("bind\s+--\s+(.+):\s+(.+)")

    def __init__(self, db):
        self.db = db
        self.name = "jam -dm parser"
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

    def parse_logfile(self, filename):
        """Open the supplied logfile and parse any '-dm' debug output into
        the DB"""
        # Open the file
        try:
            f = open(filename, errors="ignore")
        except:
            # The file cannot be opened.
            print("Unable to open file %s" % filename)
            raise
        else:
            # Read each line in from the logfile
            for line in f:
                self.parse_line(line)
            f.close()

    def parse_line(self, line):
        """Read the supplied line from a jam debug log file and parse it
        for -dm debug to update the DB with."""

        # The output we are interested in takes one of the following forms:
        # make -- <target>
        # time -- <target>:timestamp
        # made [stable|update] <target>
        # bind -- <target>:filename
        #
        # Call the parse functions for each of these in turn (apart from the
        # 'make' line which is entirely uninteresting).
        self.parse_time_line(line)
        self.parse_made_line(line)
        self.parse_bind_line(line)

    def parse_time_line(self, line):
        m = self._time_re.match(line)
        if m:
            target_name = m.group(1)
            timestamp = m.group(2)

            target = self.db.get_target(target_name)
            # See `target_bind` in jam. A timestamp is output only for "exists"
            # and not the other binding states.
            if timestamp not in {"missing", "unbound", "parents"}:
                dt = datetime.strptime(timestamp, "%a %b %d %H:%M:%S %Y")
                target.set_timestamp(dt)

    def parse_bind_line(self, line):
        m = self._bind_re.match(line)
        if m:
            target_name = m.group(1)
            bind_target = m.group(2)

            target = self.db.get_target(target_name)
            target.set_binding(bind_target)

    def parse_made_line(self, line):
        m = self._made_re.match(line)
        if m:
            fate_name = m.group(1)
            target_name = m.group(2)

            target = self.db.get_target(target_name)
            fate = database.Fate(fate_name)
            target.set_fate(fate)
