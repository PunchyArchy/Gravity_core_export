from gravity_core.tests.sqlhell_test import shell
from gravity_core.support_funcs import *

shell.debug = True
old_carnum = 'В060ХА703'
new_carnum = 'В060ХА705'
if not check_car_registered(shell, new_carnum):
    register_new_car(shell, new_carnum)
change_rfid(shell, new_carnum, old_carnum)
