#------------------------------------------------------------------------------
# database.py - Database module
#
# November 2015, Phil Connell
#------------------------------------------------------------------------------

"""Target database."""

__all__ = (
    "Database",
    "Target",
    "Rule",
    "RuleCall"
)


import collections
import re


class Database:
    """Database of jam targets."""

    # Mapping from target names to targets.
    _targets = None
    _rules = None

    def __init__(self):
        self._targets = collections.OrderedDict()
        self._rules = collections.OrderedDict()

    def __repr__(self):
        return "{}({} targets, {} rules)".format(type(self).__name__,
                                                 len(self._targets),
                                                 len(self._rules))

    def get_target(self, name):
        """Get a target with a given name, creating it if necessary."""
        try:
            target = self._targets[name]
        except KeyError:
            target = Target(name)
            self._targets[name] = target
        return target

    def find_targets(self, name_regex):
        """Iterator that yields all targets whose name matches a regex."""
        for name, target in self._targets.items():
            try:
                if re.search(name_regex, name):
                    yield target
            except re.error as e:
                raise ValueError(str(e))

    def find_rebuilt_targets(self, name_regex):
        """Iterator that yields all targets whose name matches a regex and
           have their rebuilt flag set to True."""
        for target in self.find_targets(name_regex):
            if target.rebuilt:
                yield target

    def get_rule(self, name):
        """Get a rule with a given name, returns None if not existant"""
        rule = None
        if name in self._rules:
            rule = self._rules[name]
        return rule

    def declare_rule(self, name):
        """
        Add a new rule to the database if it does not already exist.
        Return the new or existing rule object.
        """
        rule = None
        if name in self._rules:
            rule = self._rules[name]
        else:
            rule = Rule(name)
            self._rules[name] = rule
        return rule

    def find_rules(self, name_regex):
        """Iterator that yields all rules whose name matches a regex."""
        for name, rule in self._rules.items():
            try:
                if re.search(name_regex, name):
                    yield rule
            except re.error as e:
                raise ValueError(str(e))


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

    .. attribute:: timestamp_chain

        Sequence of targets that this target inherits its timestamp from.

    .. attribute:: variables

        OrderedDict of the target specific variables and their values

    .. attribute:: rule_calls

        OrderedDict containing information on the rule calls for this target

    """

    def __init__(self, name):
        self.name = name
        self.deps = []
        self.deps_rev = set()
        self.incs = []
        self.incs_rev = set()
        self.timestamp = None
        self.binding = None
        self.rebuilt = False
        self.rebuild_info = RebuildInfo()
        self.timestamp_chain = None
        self.variables = collections.OrderedDict()
        self.rule_calls = collections.OrderedDict()

    def __repr__(self):
        return "{}({})".format(type(self).__name__, self.name)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def add_dependency(self, other):
        """Record the target 'other' as depended on by this target."""
        # Dependencies may be parsed more than once, but only one copy allowed
        if self not in other.deps_rev:
            self.deps.append(other)
            other.deps_rev.add(self)

    def add_inclusion(self, other):
        """Record the target 'other' as included by this target."""
        # Inclusions may be parsed more than once, but only one copy allowed
        if self not in other.incs_rev:
            self.incs.append(other)
            other.incs_rev.add(self)

    def brief_name(self):
        """Return a summarised version of this target's name."""
        # For now, just strip out most of the grist.
        grist, filename = self._grist_and_filename()
        if grist.count("!") > 1:
            brief_grist = "{}!{}!...>".format(
                *grist.split("!", maxsplit=2)[:2])
        else:
            brief_grist = grist
        return brief_grist + filename

    def filename(self):
        """Return the file name for this target (i.e. strip off gristing)."""
        return self._grist_and_filename()[1]

    def grist(self):
        """Return this target's grist."""
        return self._grist_and_filename()[0]

    def _grist_and_filename(self):
        """Split this target's name into a grist and filename."""
        if self.name.startswith("<"):
            grist, filename = self.name.split(">", maxsplit=1)
            return grist + ">", filename
        else:
            return "", self.name

    def set_timestamp(self, timestamp):
        """Set the updated timestamp on this target."""
        self.timestamp = timestamp

    def set_binding(self, binding):
        """Set the file binding for this target"""
        self.binding = binding

    def set_rebuilt(self):
        """Mark this target as having been rebuilt"""
        self.rebuilt = True

    def set_rebuilt_reason(self, reason):
        """Set the rebuild reason of this target"""
        self.rebuild_info.reason = reason

    def set_rebuilt_dep(self, dep):
        """ Mark this target as having been rebuilt due to dependency
            being updated """
        self.rebuilt = True
        self.rebuild_info.reason = "Dependency updated"
        self.rebuild_info.dep = dep

    def set_var_value(self, variable_name, values):
        """ Set the target specific variable 'variable_name' on this target to
            'values[]' """
        self.variables[variable_name] = values

    def add_rule_call(self, target_type, rule_call):
        """ Add the rule call to the relevant list for this target """
        if target_type not in self.rule_calls:
            self.rule_calls[target_type] = list()
        self.rule_calls[target_type].append(rule_call)


class RebuildInfo:
    """
    Class containing information related to rebuilds
    """
    def __init__(self):
        self.reason = None
        self.dep = None

    def __repr__(self):
        return "{}(reason={}, dep={})".format(
            type(self).__name__, self.reason, self.dep)


class Rule:
    """
    Class containing information related to Jam rules

    .. attribute:: name

        Name of the Rule

    .. attribute:: calls

        List of RuleCalls for this rule

    """
    def __init__(self, name):
        self.name = name
        self.calls = list()

    def __repr__(self):
        return "{}(name={})".format(type(self).__name__, self.name)

    def add_call(self, db, arg_list):
        """
        Add information about the call of a rule with a list of string
        containing the argument list (colon seperated as in jam)
        """
        new_rule = RuleCall(self, db, arg_list)
        self.calls.append(new_rule)
        return new_rule


class RuleCall:
    """
    Class containing information related to the call of a Jam rule

    .. attribute:: rule

        Rule object that this is a call of

    .. attribute:: args

        List of the used arguments for this call.
        Each argument is a list of Target objects.

    """
    def __init__(self, rule, db, arg_list):
        self.rule = rule
        self.caller = None
        self.sub_calls = list()
        self.args = list()
        self.args.append(list())
        arg_index = 0
        for element in arg_list:
            if element == ":":
                self.args.append(list())
                arg_index += 1
            else:
                target = db.get_target(element)
                self.args[arg_index].append(target)
                if arg_index == 0:
                    target.add_rule_call("target", self)
                elif arg_index == 1:
                    target.add_rule_call("source", self)
                else:
                    target.add_rule_call("other", self)

    def __repr__(self):
        if len(self.args[0]) > 1:
            return "{} {} ...".format(self.rule.name, self.args[0][0].brief_name())
        if len(self.args[0]) == 1:
            return "{} {}".format(self.rule.name, self.args[0][0].brief_name())
        else:
            return "{}".format(self.rule.name)

    def set_caller(self, caller):
        """
        Set the rule call that in turn called this instance of the rule
        """
        assert self.caller is None
        self.caller = caller

    def add_sub_call(self, call):
        """
        Add a rule call to the list of rules this instance of the rule calls
        """
        self.sub_calls.append(call)

    def get_targets(self):
        """
        Get all elements passed as 1st arg
        """
        if len(self.args) > 0:
            return self.args[0]
        else:
            return []

    def get_source_targets(self):
        """
        Get all elements passed as 2nd arg
        """
        if len(self.args) > 1:
            return self.args[1]
        else:
            return []

    def get_other_targets(self):
        """
        Get all elements passed as 3rd or higher arg
        """
        return self.args[2:]

