from gravity_core.functions import duo_functions
from gravity_core import wsettings as s


def update_opened_record(sqlshell, record_id, car_number, carrier, trash_cat, trash_type,
                         comment, records_table=s.records_table, records_owning_table=s.records_owning_table,
                         pol_owners_table=s.pol_owners_table, polygon=None, *args, **kwargs):
    """ Изменить запись, у которой уже есть брутто """
    command = "UPDATE {} SET car_number='{}', carrier={}, trash_cat={}, trash_type={}, notes='{}' " \
              "WHERE id={} and inside=True"
    command = command.format(records_table, car_number, carrier, trash_cat, trash_type, comment, record_id)
    sqlshell.try_execute(command)
    if polygon and records_owning_table and pol_owners_table:
        # Если поддерживается DUO - изменить присваивание
        duo_functions.records_owning_save(sqlshell, records_owning_table, pol_owners_table, polygon, record_id)
