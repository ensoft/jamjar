#------------------------------------------------------------------------------
# __init__.py - Parsers package root
#
# December 2015, Antony Wallace
#------------------------------------------------------------------------------

"""Parsers for Jam debug output."""

__all__ = (
    "parse",
)


from ._dd import DDParser
from ._dm import DMParser
from ._dc import DCParser
from ._d5 import D5Parser


def parse(db, logfile, parsers):
    """
    Parse as much information as possible from the given log file into a DB.

    :param db:
        Target database to populate.
    :param logfile:
        Source jam log file containing debug output.

    """
    parser_clses = {
        "d":DDParser,
        "c":DCParser,
        "3":DMParser,
        "5":D5Parser,
    }

    # Get which parsers to run from the command line option
    parsers_to_run = set()
    parsers = list(parsers)
    if "m" in parsers:
        # The 'm' option is the same as the +3 option
        # replace m for +3 for numerical options to work
        parsers.append("+")
        parsers.append("3")
        parsers.remove("m")
    for i in range(len(parsers)):
        if parsers[i].isdigit():
            # Handle numerical options
            if (i > 0 and parsers[i-1] == "+"):
                # Specific numerical level given
                if parsers[i] in parser_clses:
                    parsers_to_run.add(parser_clses[parsers[i]])
                else:
                    print("No parser exists for option +{}".format(parsers[i]))
            else:
                # Run all available parsers up to given number
                for num in range(2,int(parsers[i])+1):
                    if str(num) in parser_clses:
                        parsers_to_run.add(parser_clses[str(num)])
                    else:
                        print("No parser exists for option +{}".format(num))
        else:
            # Handle alphabetic options
            if parsers[i] in parser_clses:
                parsers_to_run.add(parser_clses[parsers[i]])
            elif parsers[i] != "+":
                print("No parser exists for option {}".format(parsers[i]))


    for parser_cls in parsers_to_run:
        print("Running {}".format(parser_cls.__name__))
        parser_cls(db).parse_logfile(logfile)

