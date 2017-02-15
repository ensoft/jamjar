#------------------------------------------------------------------------------
# ui.py - CLI commands module
#
# November 2015, Zoe Kelly
#------------------------------------------------------------------------------

import cmd, sys, io, pydoc

from . import database, query


class _BaseCmd(cmd.Cmd):
    """Base class for command submodes."""
    def __init__(self, paging_on):
        super().__init__()
        self.paging_on = paging_on
        self.out = None
        if paging_on == True:
            self.turn_paging_on()
        else:
            self.turn_paging_off()

    def onecmd(self, line):
        """
        Execute a single command.

        This is overridden to allow ctrl-c to interrupt long-running commands,
        without exiting.

        """
        try:
            return super().onecmd(line)
        except KeyboardInterrupt:
            pass

    def turn_paging_on(self):
        self.paging_on = True

    def turn_paging_off(self):
        self.paging_on = False
        sys.stdout = sys.__stdout__

    def precmd(self, line):
        self.start_pager()
        return (line)

    def start_pager(self):
        if self.paging_on:
            self.out = io.StringIO()
            sys.stdout = self.out

    def postcmd(self, stop, line):
        self.flush_pager()
        return (stop)

    def flush_pager(self):
       # Reset
        sys.stdout = sys.__stdout__

        if self.paging_on:
            # Page output of this command
            if self.out is not None:
                pydoc.pager(self.out.getvalue())
        self.out = None

    def do_paging_off(self, arg):
        """"Turn paging off"""
        self.turn_paging_off()

    def do_paging_on(self, arg):
        """Turn paging on"""
        self.turn_paging_on()

    def do_EOF(self, arg):
        """Handle EOF (AKA ctrl-d)."""
        print("")
        return self.do_exit(None)

    def do_exit(self, arg):
        """Exit this submode."""
        return True

    def format_prompt(self, prompt_string, color):
        """
        Utility to easily create colored prompt message for modes
        """
        escapes = {
            "red":"\x1b[31m",
            "green":"\x1b[32m",
            "yellow":"\x1b[33m",
            "blue":"\x1b[34m",
            "magenta":"\x1b[35m",
            "cyan":"\x1b[36m",
            "none":"\x1b[0m",
        }
        if sys.stdout.isatty():
            return "({}{}{}) ".format(escapes[color],
                                      prompt_string,
                                      escapes["none"])
        else:
            return "({}) ".format(prompt_string)


class UI(_BaseCmd):
    def __init__(self, db, *, paging_on=False):
        super().__init__(paging_on)
        self.file = None
        self.intro = "Welcome to JamJar.  Type help or ? to list commands.\n"
        self.prompt = self.format_prompt("jamjar", "green")
        self.database = db

    def do_targets(self, target_string):
        """Get information about targets matching a regex."""
        try:
            target_list = list(self.database.find_targets(target_string))
        except ValueError as e:
            print("Invalid target string: {}".format(str(e)))
            return
        if len(target_list) == 0:
            print("No targets found")
        elif len(target_list) == 1:
            TargetSubmode(target=target_list[0],
                          paging_on=self.paging_on,
                          db=self.database).cmdloop()
        else:
            target = self._target_selection(target_list)
            if target is not None:
                TargetSubmode(target=target,
                              paging_on=self.paging_on,
                              db=self.database).cmdloop()

    def do_rebuilt_targets(self, target_string):
        """Get information about targets that were rebuilt matching a regex."""
        try:
            target_list = list(self.database.find_rebuilt_targets(target_string))
        except ValueError as e:
            print("Invalid target string: {}".format(str(e)))
            return
        if len(target_list) == 0:
            print("No targets found")
        elif len(target_list) == 1:
            TargetSubmode(target=target_list[0],
                          paging_on=self.paging_on,
                          db=self.database).cmdloop()
        else:
            target = self._target_selection(target_list)
            if target is not None:
                TargetSubmode(target=target,
                              paging_on=self.paging_on,
                              db=self.database).cmdloop()

    def _target_selection(self, targets):
        for idx, target in enumerate(targets):
            print("({}) {}".format(idx , target))
        self.flush_pager()

        target = None
        while True:
            try:
                choice = input("Choose target (range 0:{}): ".format(
                    len(targets) - 1))
            except EOFError:
                print("")
                break
            # Exit target selection on empty input.
            if not choice:
                break
            try:
                target_index = int(choice)
                target = targets[target_index]
            except (ValueError, IndexError):
                pass
            else:
                break
        return target

    def do_rules(self, rule_string):
        """Get information about rules matching a regex."""
        try:
            rules_list = list(self.database.find_rules(rule_string))
        except ValueError as err:
            print("Invalid rule string: {}".format(str(err)))
            return
        if len(rules_list) == 0:
            print("No rules found")
        elif len(rules_list) == 1:
            RuleSubmode(rule=rules_list[0],
                        paging_on=self.paging_on,
                        db=self.database).cmdloop()
        else:
            rule = self._rule_selection(rules_list)
            if rule is not None:
                RuleSubmode(rule=rule,
                            paging_on=self.paging_on,
                            db=self.database).cmdloop()

    def _rule_selection(self, rules):
        for idx, rule in enumerate(rules):
            print("({}) {}".format(idx, rule))
        self.flush_pager()

        rule = None
        while True:
            try:
                choice = input("Choose rule (range 0:{}): ".format(
                    len(rules) - 1))
            except EOFError:
                print("")
                break
            # Exit rule selection on empty input
            if not choice:
                break
            try:
                rule_index = int(choice)
                rule = rules[rule_index]
            except (ValueError, IndexError):
                pass
            else:
                break
        return rule


class TargetSubmode(_BaseCmd):
    """ Submode to interact with a particular target """
    def __init__(self, target, *, paging_on, db=None):
        super().__init__(paging_on)
        self.target = target
        self.prompt = self.format_prompt(self.target.brief_name(), "green")
        self.database = db

    def do_switch_to_target(self, target_string):
        """Switch to the TargetSubmode for the specified target"""
        try:
            target_list = list(self.database.find_targets(target_string))
        except ValueError as err:
            print("Invalid target string: {}".format(str(err)))
            return
        if len(target_list) == 0:
            print("No targets found")
        elif len(target_list) == 1:
            TargetSubmode(target=target_list[0],
                          paging_on=self.paging_on,
                          db=self.database).cmdloop()
            return True
        else:
            target = None
            for targ in target_list:
                if targ.name == target_string:
                    target = targ
            if target != None:
                TargetSubmode(target=target,
                              paging_on=self.paging_on,
                              db=self.database).cmdloop()
                return True
            else:
                print("Target {} not found".format(target_string))

    def do_deps(self, arg):
        """
        Show all direct dependencies, including those arising from includes.
        """
        self._print_targets(query.deps(self.target))

    def do_deps_rebuilt(self, arg):
        """Show direct dependencies that have been rebuilt."""
        self._print_targets(query.deps_rebuilt(self.target))

    def do_dep_chains(self, arg):
        """Show all chains of dependencies below this target."""
        # Yuck.
        kwargs = self._arg_to_kwargs(arg)
        if "max_depth" in kwargs:
            kwargs["max_depth"] = int(kwargs["max_depth"])
        for chain in query.dep_chains(self.target, **kwargs):
            self._print_chain(chain)

    def do_dep_chains_rebuilt(self, arg):
        """Show all chains of dependencies below this target."""
        for chain in query.dep_chains_rebuilt(self.target):
            self._print_chain(chain)

    def do_rebuild_chains(self, arg):
        """Show Jam's view on why this target was rebuilt."""
        for chain in query.rebuild_chains(self.target):
            self._print_chain(chain)

    def do_show(self, arg):
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
        print("variables:")
        for key in self.target.variables:
            print("    {} = {}".format(key, self.target.variables[key]))
        if "target" in self.target.rule_calls:
            print("target of:")
            for rule_name in self.target.rule_calls["target"]:
                print("    {}".format(rule_name))
        if "source" in self.target.rule_calls:
            print("source for:")
            for rule_name in self.target.rule_calls["source"]:
                print("    {}".format(rule_name))
        if "other" in self.target.rule_calls:
            print("higher ordered target in:")
            for rule_name in self.target.rule_call["other"]:
                print("    {}".format(rule_name))
        if (self.target.timestamp_chain is not None and
                len(self.target.timestamp_chain) > 0):
            print("timestamp:", self.target.timestamp_chain[-1].timestamp)
            print("timestamp inherited from:")
            self._print_targets(self.target.timestamp_chain)
        else:
            print("timestamp:", self.target.timestamp)
        print("binding:", self.target.binding)
        print("rebuilt:", self.target.rebuilt)
        if self.target.rebuilt:
            print("    rebuilt reason:", self.target.rebuild_info.reason)
            if self.target.rebuild_info.dep is not None:
                print("    dependency:", self.target.rebuild_info.dep.name)

    def do_alternative_grists(self, arg):
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

    def _arg_to_kwargs(self, arg):
        """Parse an input argument consisting of param=value pairs."""
        kwargs = {}
        args = arg.split()
        for arg in args:
            key, value = arg.split("=")
            kwargs[key] = value
        return kwargs

    def _print_chain(self, chain):
        """Print a sequence of targets forming a dependency chain."""
        print(" -> ".join(target.name for target in chain))

    def _print_targets(self, targets):
        """Print a sequence of targets."""
        for target in targets:
            print("    {}".format(target.name))

class RuleSubmode(_BaseCmd):
    """ Submode to interact with a jam rule """
    def __init__(self, rule, *, paging_on, db=None):
        super().__init__(paging_on)
        self.rule = rule
        self.database = db
        self.prompt = self.format_prompt(self.rule.name, "green")

    def do_switch_to_target(self, target_string):
        """Switch to the TargetSubmode for the specified target"""
        try:
            target_list = list(self.database.find_targets(target_string))
        except ValueError as err:
            print("Invalid target string: {}".format(str(err)))
            return
        if len(target_list) == 0:
            print("No targets found")
        elif len(target_list) == 1:
            TargetSubmode(target=target_list[0],
                          paging_on=self.paging_on,
                          db=self.database).cmdloop()
            return True
        else:
            target = None
            for targ in target_list:
                if targ.name == target_string:
                    target = targ
            if target != None:
                TargetSubmode(target=target,
                              paging_on=self.paging_on,
                              db=self.database).cmdloop()
                return True
            else:
                print("Target {} not found".format(target_string))

    def do_show(self, arg):
        """Dump all available information for this rule."""
        print("name:", self.rule.name)
        print("number of calls:", len(self.rule.calls))

    def do_calls(self, arg):
        """Show all calls of this rule. Switch to selected RuleCallSubmode"""
        for idx, call in enumerate(self.rule.calls):
            print("({}) {}".format(idx, call))
        self.flush_pager()

        call = None
        while True:
            try:
                choice = input("Choose call (range 0:{}): ".format(
                    len(self.rule.calls) - 1))
            except EOFError:
                print("")
                break
            # Exit call selection on empty input
            if not choice:
                break
            try:
                call_index = int(choice)
                call = self.rule.calls[call_index]
            except (ValueError, IndexError):
                pass
            else:
                break

        if call is not None:
            RuleCallSubmode(call=call,
                            paging_on=self.paging_on).cmdloop()


class RuleCallSubmode(_BaseCmd):
    """ Submode to interact with a particular rule call """
    def __init__(self, call, *, paging_on, db=None):
        super().__init__(paging_on)
        self.call = call
        self.database = db
        self.prompt = self.format_prompt(self.call, "green")

    def do_show(self, arg):
        """Dump all available information about this rule call"""
        self.do_targets(arg)
        self.do_sources(arg)
        if len(self.call.get_other_targets()) != 0:
            print("Others:")
            index = 3
            for arg in self.call.get_other_targets():
                print("  Arg {}:".format(index))
                print(arg)
                index += 1
                for target in arg:
                    print("    {}".format(target.name))
        print("Called by:")
        print("    {}".format(self.call.caller))
        if len(self.call.sub_calls) != 0:
            print("Calls:")
            for call in self.call.sub_calls:
                print("    {}".format(call))

    def do_targets(self, arg):
        """List all the targets used as targets in this call"""
        print("Targets:")
        for target in self.call.get_targets():
            print("    {}".format(target.name))

    def do_sources(self, arg):
        """List all the targets used as sources in this call"""
        print("Sources:")
        for source in self.call.get_source_targets():
            print("    {}".format(source.name))

    def do_call_stack(self, arg):
        """Display the call stack that laid to this call"""
        stack = list()
        caller = self.call.caller
        while caller:
            stack.append(caller)
            caller = caller.caller
        while len(stack) > 0:
            print(stack.pop())

