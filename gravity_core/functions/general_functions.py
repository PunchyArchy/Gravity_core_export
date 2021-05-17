from gravity_core.functions import duo_functions

def update_opened_record(sqlshell, record_id, car_number, carrier, trash_cat, trash_type,
                         comment, records_table, records_owning_table=None, pol_owners_table=None, polygon=None):
    """ Изменить запись, у которой уже есть брутто """
    command = "UPDATE {} SET car_number='{}', carrier={}, trash_cat={}, trash_type={}, notes='{}' " \
              "WHERE id={} and inside=True"
    command = command.format(records_table, car_number, carrier, trash_cat, trash_type, comment, record_id)
    sqlshell.try_execute(command)
    if polygon and records_owning_table and pol_owners_table:
        # Если поддерживается DUO - изменить присваивание
        duo_functions.records_owning_save(sqlshell, records_owning_table, pol_owners_table, polygon, record_id)
