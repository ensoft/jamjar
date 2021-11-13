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


from ._base import BaseParser


class DDParser(BaseParser):
    def parse_logfile(self, filename, debug_flag=False):
        """
        Function to parse log files with '-dd' debug output.

        Currently can read:

        Depends x:y
        Includes x:y"""

        with open(filename, errors="ignore") as f:
            for line in f:
                # Depending on the first word, add the relevant information to the database
                #
                # x depends on y
                # x includes y

                first_word = line.split(" ", 1)[0]

                if first_word == "Depends" or first_word == "Includes":
                    x_y = line.split(" ", 1)[1]
                    x_garbage = x_y.split('" : "', 1)[
                        0
                    ]  # includes the prefix '\"' which needs to be removed
                    y_garbage = x_y.split('" : "', 1)[
                        1
                    ]  # includes an ending '\" ;' which needs to be removed

                    x = x_garbage.replace('"', "")
                    y = y_garbage.replace('" ;', "").replace("\n", "")

                    # Debug
                    if debug_flag == True:
                        if first_word == "Depends":
                            print(x, "depends on", y)
                        elif first_word == "Includes":
                            print(x, "includes", y)

                    # Add to the database
                    x_target = self.db.get_target(x)
                    y_target = self.db.get_target(y)

                    if first_word == "Depends":
                        x_target.add_dependency(y_target)
                    elif first_word == "Includes":
                        x_target.add_inclusion(y_target)
        return None
