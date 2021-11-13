# ------------------------------------------------------------------------------
# ui.py - CLI commands module
#
# November 2015, Zoe Kelly
# ------------------------------------------------------------------------------

"""Command interpreter UI."""

__all__ = ("UI",)

import cmd
import sys

from typing import Any, Iterable, Optional

from . import database
from . import query


class _BaseCmd(cmd.Cmd):
    """Base class for command submodes."""

    def do_EOF(self, _: Any) -> bool:
        """Handle EOF (AKA ctrl-d)."""
        print("")
        return self.do_exit(None)

    def do_exit(self, _: Any) -> bool:
        """Exit this submode."""
        return True

    def format_prompt(self, prompt_string: str, color: str) -> str:
        """
        Utility to easily create colored prompt message for modes
        """
        escapes = {
            "red": "\x1b[31m",
            "green": "\x1b[32m",
            "yellow": "\x1b[33m",
            "blue": "\x1b[34m",
            "magenta": "\x1b[35m",
            "cyan": "\x1b[36m",
            "none": "\x1b[0m",
        }
        if sys.stdout.isatty():
            return "({}{}{}) ".format(
                escapes[color], prompt_string, escapes["none"]
            )
        else:
            return "({}) ".format(prompt_string)


class UI(_BaseCmd):
    def __init__(self, db: database.Database) -> None:
        super().__init__()
        self.intro = "Welcome to JamJar.  Type help or ? to list commands.\n"
        self.prompt = self.format_prompt("jamjar", "green")
        self.database = db

    def do_targets(self, match: str) -> None:
        """Get information about targets matching a regex."""
        try:
            targets = list(self.database.find_targets(match))
        except ValueError as e:
            print(f"Invalid target search input: {e}")
        else:
            self._maybe_enter_target_submode(targets)

    def do_rebuilt_targets(self, match: str) -> None:
        """Get information about targets that were rebuilt matching a regex."""
        try:
            targets = list(self.database.find_rebuilt_targets(match))
        except ValueError as e:
            print(f"Invalid target search input: {e}")
        else:
            self._maybe_enter_target_submode(targets)

    def _maybe_enter_target_submode(
        self, candidates: list[database.Target]
    ) -> None:
        """
        Select from targets, entering the target submode if one is selected.
        """
        target: Optional[database.Target] = None
        if not candidates:
            print("No targets found")
        elif len(candidates) == 1:
            target = candidates[0]
        else:
            target = self._select_target(candidates)
        if target is not None:
            TargetSubmode(target, self.database, parent=self).cmdloop()

    def _select_target(
        self, targets: list[database.Target]
    ) -> Optional[database.Target]:
        """Prompt the user to select a target."""
        for idx, target in enumerate(targets):
            print("({}) {}".format(idx, target))

        while True:
            try:
                choice = input(
                    "Choose target (range 0:{}): ".format(len(targets) - 1)
                )
            except EOFError:
                print("")
                break
            else:
                if not choice:
                    break

            try:
                return targets[int(choice)]
            except (ValueError, IndexError):
                pass

        return None


class TargetSubmode(_BaseCmd):
    """Submode to interact with a particular target"""

    def __init__(
        self, target: database.Target, db: database.Database, *, parent: UI
    ):
        super().__init__()
        self.target = target
        self.prompt = self.format_prompt(self.target.brief_name(), "green")
        self.database = db
        self.parent = parent

    def do_switch(self, match: str) -> None:
        """Switch to the TargetSubmode for the specified target."""
        self.parent.do_targets(match)

    def do_deps(self, _: Any) -> None:
        """
        Show all direct dependencies, including those arising from includes.
        """
        self._print_targets(query.deps(self.target))

    def do_deps_rebuilt(self, _: Any) -> None:
        """Show direct dependencies that have been rebuilt."""
        self._print_targets(query.deps_rebuilt(self.target))

    def do_rebuild_chains(self, _: Any) -> None:
        """Show Jam's view on why this target was rebuilt."""
        for chain in query.rebuild_chains(self.target):
            self._print_rebuild_chain(chain)
            timestamp_chain = query.timestamp_inheritance_chain(chain[-1][0])
            if timestamp_chain is not None:
                print("")
                self._print_timestamp_chain(timestamp_chain)

    def do_show(self, _: Any) -> None:
        """Dump all available meta-data for this target."""
        print("name:", self.target.name)
        print("depends on:")
        self._print_targets(self.target.deps)
        print("depended on by:")
        self._print_targets(self.target.deps_rev)
        print("includes:")
        self._print_targets(self.target.incs)
        print("included by:")
        self._print_targets(self.target.incs_rev)
        print("newer than:")
        self._print_targets(self.target.newer_than)
        print("older than:")
        self._print_targets(self.target.older_than)
        print("timestamp:", self.target.timestamp)
        if self.target.inherits_timestamp_from is not None:
            print(
                "inherits timestamp from:", self.target.inherits_timestamp_from
            )
        if self.target.bequeaths_timestamp_to:
            print("bequeaths timestamp to:")
            for inheritor in sorted(
                self.target.bequeaths_timestamp_to, key=lambda tgt: tgt.name
            ):
                print("    {}".format(inheritor))
        print("binding:", self.target.binding)
        if self.target.fate is not None:
            print("fate:", self.target.fate.value)
        if self.target.rebuild_reason is not None:
            print("rebuild reason:", self.target.rebuild_reason.value)
            if self.target.rebuild_reason_target:
                print("    due to:", self.target.rebuild_reason_target.name)

    def do_alternative_grists(self, _: Any) -> None:
        """
        Show the grists of all the targets with the same
        filename as the current target.
        """
        filename = self.target.filename()
        targets = list(self.database.find_targets(filename))
        grists = list()
        for target in targets:
            if target.filename() == filename:
                grists.append(target.grist())
        grists.sort()
        for grist in grists:
            print("    {}".format(grist))

    def _print_rebuild_chain(self, chain: query.RebuildChain) -> None:
        """Print a sequence of targets forming a dependency chain."""
        links = []
        for target, reason in chain:
            if reason is None:
                links.append(target.name)
            else:
                links.append(f"{target.name} ({reason.value})")
        print("\n -> ".join(links))

    def _print_timestamp_chain(self, chain: query.Chain) -> None:
        """Print a sequence of targets forming a timestamp inheritance chain."""
        print("{} inherits its timestamp from:".format(chain[0]))
        links = (target.name for target in chain[1:])
        print("\n -> ".join(links))

    def _print_targets(self, targets: Iterable[database.Target]) -> None:
        """Print a sequence of targets."""
        for target in targets:
            print("    {}".format(target.name))
