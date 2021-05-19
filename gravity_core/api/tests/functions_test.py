from gravity_core.api.functions import get_unfinished_cycles
from gravity_core.tests.sqlhell_test import shell


def get_unfinished_cycles_test():
    response = get_unfinished_cycles(shell)
    print(response)


get_unfinished_cycles_test()