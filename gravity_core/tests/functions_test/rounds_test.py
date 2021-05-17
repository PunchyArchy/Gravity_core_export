from gravity_core.functions.round_functions import check_car_inside
from gravity_core.tests.sqlhell_test import shell


def check_car_inside_test():
    return check_car_inside(shell, 'У881УК1ff02', 'records')

