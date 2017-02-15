#------------------------------------------------------------------------------
# _d+5.py
#
# Parser for the jam '+5' debug flag output - which contains details of
# rule flow and variable values
#
# January 2017, Oliver Johnson
#------------------------------------------------------------------------------

'''jam -d+5 output parser'''

from ._base import BaseParser

__all__ = (
    "D5Parser",
)

class D5Parser(BaseParser):
    '''
    Parser the jam '+5' debug flag output from a logfile into the DB supplied
    at initialisation.

    .. attribute:: name

        Name of this parser.

    Currently can read:

    >>.. rule RuleName
    >>.. RuleName {args...}
    >>.. set VARIABLE on Targets ... = Values ...
    >>.. Depends/DEPENDS ... : ...
    >>.. Includes/INCLUDES ... : ...
    '''
    def __init__(self, db):
        BaseParser.__init__(self, db)
        self.name = "jam -d+5 parser"
        self.rule_stack = [dict()]

    def parse_logfile(self, filename):
        '''
        Function to parse log files with '-d+5' debug output.
        '''
        self.rule_stack = [dict()]

        with open(filename, errors="ignore") as logfile:
            for line in logfile:
                self.parse_line(line)
        return None

    def parse_line(self, line):
        """Read the supplied line from a jam debug log file and parse it"""
        words = line.split()
        if len(words) < 2:
            # No interest in single word lines
            return

        if not words[0].startswith(">"):
            # Not a d5 output line
            return

        # Handle the rule stack
        while len(self.rule_stack) > self.get_rule_depth(words[0]):
            self.rule_stack.pop()
        self.rule_stack.append({"line":line})

        # Run the parsers
        if self.parse_decl_line(words):
            return
        if self.parse_set_line(words):
            return
        if self.parse_dep_line(words):
            return
        if self.parse_inc_line(words):
            return
        if self.parse_call_line(words):
            return

    def parse_decl_line(self, words):
        ''' parsing ">>.. rule RuleName" '''
        if words[1] == "rule" and len(words) == 3:
            rule_name = words[2]
            self.db.declare_rule(rule_name)
            return True
        else:
            return False

    def parse_set_line(self, words):
        '''
        parsing:
        ">>.. set VARIABLE on Target1 Target2 ... = {Values...}"
        '''
        if (len(words) > 5
                and words[1] == "set"
                and words[3] == "on"
                and "=" in words[5:]):
            variable_name = words[2]
            target_names = words[4:words.index("=")]
            for target_name in target_names:
                targ = self.db.get_target(target_name)
                targ.set_var_value(variable_name, words[words.index("=")+1:])
            return True
        else:
            return False

    def parse_dep_line(self, words):
        '''
        parsing:
        ">>.. Depends x ... : y ..."
        '''
        if (len(words) > 3
                and (words[1] == "Depends" or words[1] == "DEPENDS")
                and ":" in words[3:]):
            for x_string in words[2:words.index(":")]:
                x_targ = self.db.get_target(x_string)
                for y_string in words[words.index(":")+1:]:
                    y_targ = self.db.get_target(y_string)
                    x_targ.add_dependency(y_targ)
            return True
        else:
            return False

    def parse_inc_line(self, words):
        '''
        parsing:
        ">>.. Includes x ... : y ..."
        '''
        if (len(words) > 3
                and (words[1] == "Includes" or words[1] == "INCLUDES")
                and ":" in words[3:]):
            for x_string in words[2:words.index(":")]:
                x_targ = self.db.get_target(x_string)
                for y_string in words[words.index(":")+1:]:
                    y_targ = self.db.get_target(y_string)
                    x_targ.add_inclusion(y_targ)
            return True
        else:
            return False

    def parse_call_line(self, words):
        ''' parsing ">>.. RuleName {args...}" '''
        if self.db.get_rule(words[1]) is not None:
            rule_object = self.db.get_rule(words[1])
            call = rule_object.add_call(self.db, words[2:])
            # Handle rule stack
            self.rule_stack[-1]["rule_call"] = call
            if len(self.rule_stack) > 1:
                if "rule_call" in self.rule_stack[-2]:
                    # Set values for caller
                    call.set_caller(self.rule_stack[-2]["rule_call"])
                    self.rule_stack[-2]["rule_call"].add_sub_call(call)
            return True
        else:
            return False

    def get_rule_depth(self, word):
        """
        Get the rule stack depth from the >| symbols in the first word of the
        d+5 output line.
        """
        # Maximum depth the stack will go with an even number of symbols
        even_stack_depth_max = 35
        if len(word) % 2 == 0:
            return int(len(word)/2)
        else:
            return int((even_stack_depth_max + len(word))/2)
