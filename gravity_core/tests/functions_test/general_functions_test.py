from gravity_core.functions.general_functions import update_opened_record
from gravity_core.tests.sqlhell_test import shell as sql_shell
from gravity_core import wsettings as s


def update_opened_record_test(record_id=2, car_number='А222АА111', carrier=1, trash_cat=4, trash_type=2,
                              comment='CHANGED FROM FUNC', polygon='ХВОСТЫ-ТЕСТ'):
    update_opened_record(sql_shell, record_id, car_number, carrier, trash_cat, trash_type, comment, s.records_table,
                         s.records_owning_table, s.pol_owners_table, polygon)


update_opened_record_test()