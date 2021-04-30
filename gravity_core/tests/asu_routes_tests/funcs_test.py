from gravity_core.functions.asu_routes import check_if_car_tko, get_tko_id, check_asu_routes
from gravity_core.tests.sqlhell_test import shell


def check_if_car_tko():
    res = check_if_car_tko(shell, 'Н628ВХ102', 'asu_routes', 'auto')
    print(res, type(res))


def get_tko_id_test():
    res = get_tko_id(shell, 'trash_cats')
    print(res)

def check_asu_routes_test():
    res = check_asu_routes(shell, 'trash_cats', 1, False, '', 'TKOio', 'oiTKO')
    print(res)

#get_tko_id_test()
check_asu_routes_test()