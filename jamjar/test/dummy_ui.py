# ------------------------------------------------------------------------------
# ui_dummy.py - Interactive UI test with stubbed database
#
# November 2015, Zoe Kelly
# ------------------------------------------------------------------------------

import re, collections

import jamjar.ui as ui


class Database:
    """Database of jam targets."""

    # Mapping from target names to targets.
    _targets = None

    def __init__(self):
        self._targets = collections.OrderedDict()
        self.target_list = ["Target1", "Target2", "Target3", "Target4"]
        for name in self.target_list:
            target = Target(name)
            self._targets[name] = target

    def find_targets(self, name_regex):
        for name, target in self._targets.items():
            if re.search(name_regex, name):
                yield target


class Target:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "{}({})".format(type(self).__name__, self.name)


if __name__ == "__main__":
    database = Database()
    ui.UI(database).cmdloop()
