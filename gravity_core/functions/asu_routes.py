""" Пакет функций для работы интеграции с АСУ по части маршрутов"""


def check_if_car_tko(sqlshell, car_number, asu_routes_table, auto_table):
    """ Возвращает True, если машина должна была привезти ТКО"""
    command = "SELECT EXISTS (SELECT car_number='{}' FROM {} WHERE car_number='{}' and count_expected > count_now)"
    command = command.format(car_number, asu_routes_table, car_number)
    response = sqlshell.try_execute_get(command)[0][0]
    return response


def get_tko_id(sqlshell, trash_cats_table, tkoname='ТКО-4'):
    """ Возвращает id ТКО из trash_cats по tkoname """
    command = "SELECT id FROM {} WHERE cat_name='{}'".format(trash_cats_table, tkoname)
    response = sqlshell.try_execute_get(command)
    return response[0][0]


def check_asu_routes(sqlshell, trash_cats_table, trash_cat, must_be_tko, alerts, tko_instead_other_text,
                     other_instead_tko_text):
    tko_id = get_tko_id(sqlshell, trash_cats_table)
    if must_be_tko and trash_cat != tko_id:
        alerts += other_instead_tko_text
    elif not must_be_tko and trash_cat == tko_id:
        alerts += tko_instead_other_text
    return alerts