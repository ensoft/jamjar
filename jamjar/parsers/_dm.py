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

from ._base import BaseParser


class DMParser(BaseParser):
    """
    Parse the jam 'm' debug flag output from a logfile into the DB supplied at
    initialisation.

    .. attribute:: name

        Name of this parser.

    """

    def __init__(self, db):
        self.db = db
        self.name = "jam -dm parser"
        # Compile the regular expressions here for speed
        self.made_re = re.compile("^made[+*]?\s+([a-z]+)\s+(.+)")
        self.make_re = re.compile("^make\s+--\s+(.+)")
        self.time_re = re.compile("^time\s+--\s+(.+):\s+(.+)")
        self.bind_re = re.compile("^bind\s+--\s+(.+):\s+(.+)")
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
        # Call the parse functions for each of these in turn
        logging.debug("Parsing line %s" % line)
        self.parse_make_line(line)
        self.parse_time_line(line)
        self.parse_made_line(line)
        self.parse_bind_line(line)

    def parse_make_line(self, line):
        # Get the target name
        m = self.make_re.match(line)
        if m:
            target_name = m.group(1)
            logging.debug("Parsing a make line for target %s" % target_name)
            target = self.db.get_target(target_name)

        # Set the 'made' flag on the target

    def parse_time_line(self, line):
        # Get the target name and the timestamp
        m = self.time_re.match(line)
        if m:
            target_name = m.group(1)
            timestamp = m.group(2)

            target = self.db.get_target(target_name)

            timestamp.replace("  ", " 0", 1)
            logging.debug("Timestamp parsed for target is %s" % timestamp)
            try:
                dt = datetime.strptime(timestamp, "%a %b %d %H:%M:%S %Y")
                # Set the timestamp
                target.set_timestamp(dt)
            except ValueError:
                logging.debug("Not a datetime")

    def parse_bind_line(self, line):
        m = self.bind_re.match(line)
        if m:
            target_name = m.group(1)
            bind_target = m.group(2)

            target = self.db.get_target(target_name)
            # Set the bind target (the file in the file system)
            target.set_binding(bind_target)

    def parse_made_line(self, line):
        m = self.made_re.match(line)
        if m:
            update = m.group(1)
            target_name = m.group(2)

            target = self.db.get_target(target_name)

            # Set the rebuilt flag
            if (
                update == "update"
                or update == "missing"
                or update == "old"
                or update == "newer"
            ):
                target.set_rebuilt()
                target.set_rebuilt_reason(update)
