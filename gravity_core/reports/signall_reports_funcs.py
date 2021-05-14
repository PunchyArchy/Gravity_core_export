""" Модуль для работы с отчетами на SignAll"""
from gravity_core.functions.tryexceptdecorator import *
from gravity_core import wsettings as s
from datetime import datetime
import os
import base64
import json


def save_json_report(sqlshell, poligon_id, tablename, filename, duo=False, pol_owner=None):
    """ Функция для сохранения отчетов (filename) в формате JSON состоящей из ключей-значений из таблицы (tablename)"""
    if tablename == 'records':
        # Если это отчеты о заездах - вызвать get_reports
        if duo:
            records, column_names = get_reports_duo(sqlshell, pol_owner)
        else:
            records, column_names = get_reports(sqlshell)
    else:
        # Если же это отчеты о машинах, юзерах или клинетах - вызвать get_records
        records, column_names = get_records(sqlshell, tablename)
    # Вернуть список словарей colnum-rec
    records_list = get_records_list(records, column_names, poligon_id)
    # Отметить, что отправили на WServer
    mark_record(sqlshell, records, tablename, 'wserver_sent', datetime.now())
    # Сохранить данные в файл
    save_json(records_list, filename, poligon_id)

def get_reports_duo(sqlshell, pol_owner):
    """Получить записи заездов с таблицы records с даты (start_date) по сегодняшний день"""
    request = 'records.id,car_number,brutto,tara,cargo, to_char("time_in",\'DD/MM/YY HH24:MI:SS\') as time_in'
    request += ',to_char("time_out",\'DD/MM/YY HH24:MI:SS\') as time_out,inside,carrier,trash_type'
    request += ',trash_cat,notes,operator,checked'
    request += ',(SELECT name FROM auto_models INNER JOIN auto ON (auto_models.id = auto.auto_model) WHERE records.car_number=auto.car_number LIMIT 1)'
    request += ', disputs.alerts'
    comm = "SELECT {} FROM {} LEFT JOIN disputs ON (disputs.records_id = records.id) " \
           "LEFT JOIN trash_cats ON (records.trash_cat = trash_cats.id) " \
           "LEFT JOIN trash_types ON (records.trash_type = trash_types.id) " \
           "LEFT JOIN duo_records_owning ON (duo_records_owning.record = records.id) " \
           "WHERE NOT (wserver_get is not null) and time_in > '14.11.2020' and not tara is null " \
           "AND duo_records_owning.owner = (SELECT id FROM duo_pol_owners WHERE name='{}') LIMIT 15".format(
        request, s.records_table, pol_owner)
    records, column_names = get_records_columns(sqlshell, comm)
    records = expand_reports_list(records)
    column_names = expand_column_names(column_names)
    return records, column_names


def get_records_list(records, column_names, poligon_id):
    """Получает запись из БД и название полей, сохраняет их в словарь вида поле:запись и
    добавляет словарь в listname, впоследствии возвращает listname"""
    listname = []
    for record in records:
        record_dict = {}
        count = 0
        for column in column_names:
            try:
                record_dict[column] = record[count]
                count += 1
            except:
                record_dict[column] = ''
                print('ERROR', column_names, record)
            # pass
        record_dict['poligon'] = poligon_id
        listname.append(record_dict)
    return listname


def mark_record(sqlshell, records, tablename, column, value):
    for rec in records:
        command = "UPDATE {} SET {}='{}' WHERE id={}".format(tablename, column, value, rec[0])
        sqlshell.try_execute(command)

def save_json(object, filepath, mode='usual'):
    """Делает дамп объекта в файл в формате JSON"""
    with open(filepath, 'w') as fobj:
        if mode == 'str':
            json.dump(object, fobj)
        else:
            json.dump(object, fobj, default=str)

def send_json_reports(sqlshell,  wclient, poligon_id, table_to_file_dict=s.json_table_to_file.items(), duo=False,
                      pol_owner=False):
    # WClient - ранее созданый WClient для связи с WServer
    # poligon_id - id полигона, полученный после аутентификации полигона на WServer
    # Получает словарь вида {'tablename'(таблица): 'tablename.json'(файл)} и сохраняет данные из таблицы в файл
    for table, filename in table_to_file_dict:
        save_json_report(sqlshell, poligon_id, table, filename, duo, pol_owner)
        wclient.send_file(filename)
        # Получить ответ от WServer. Обычно это - {'get':{'was': <wdb.records.id>, 'new': <gdb.records.id>}}
        succes_save_list = wclient.get_data()
        #if table == 'clients':
            # Ключ первичный в clients - это id_1c
        #    id_column = 'id_1c'
        #else:
            # а в остальных id
        id_column = 'id'
        print("SUCCES LIST", succes_save_list)
        mark_succes_save(sqlshell, succes_save_list, table, id_column)


def mark_succes_save(sqlshell, listname, tablename, id_column):
    """ Ответить все принятые WServer`ом данные, отметить поле id_column в таблице tablename"""
    # listname template {'get': {'was': < wdb.records.id >, 'nekw': < gdb.records.id >}}
    timenow = datetime.now()
    for record in listname:
        #print("RECORD", record)
        rec_id = record['get']['was']
        wsever_id = record['get']['now']
        command = "UPDATE {} set wserver_get='{}', wserver_id={} WHERE {}={}".format(tablename, timenow, wsever_id,
                                                                                     id_column, rec_id)
        sqlshell.try_execute(command)
        if tablename == 'records':
            remove_photo(rec_id)


def remove_photo(rec_id):
    # Удалить принятое WServer`ом фото
    in_photo_path = os.path.join(s.pics_folder, rec_id + 'IN.jpg')
    out_photo_path = os.path.join(s.pics_folder, rec_id + 'OUT.jpg')
    try_delete_photo(in_photo_path, 'Фото на въезде удалено.')
    try_delete_photo(out_photo_path, 'Фото на выезде удалено.')


def try_delete_photo(photoname, success_text, fail_text='Не удалось найти фото.'):
    """ Попытка удалить photoname. Выводит success_text если получилось, fail_text - если нет."""
    try:
        os.remove(photoname)
        print('\t', success_text)
    except FileNotFoundError:
        print('\t', fail_text)


def get_records(sqlshell, tablename, command='none'):
    """ Извлечь строки для отчета"""
    if command == 'none':
        # command = "SELECT * FROM {}".format(tablename)
        command = "SELECT * FROM {} WHERE NOT (wserver_get is not null) LIMIT 15".format(tablename)
    records, column_names = get_records_columns(sqlshell, command)
    return records, column_names


def get_records_columns(sqlshell, command):
    # Вернуть строки и имена соотсветсвтующих полей
    response = sqlshell.try_execute_get(command, mode='col_names')
    print('GOT RESPONSE', response)
    if response:
        return response[0], response[1]


def get_reports(sqlshell):
    """Получить записи заездов с таблицы records с даты (start_date) по сегодняшний день"""
    request = 'records.id, car_number, brutto, tara, cargo, to_char("time_in",\'DD/MM/YY HH24:MI:SS\') as time_in'
    request += ',to_char("time_out",\'DD/MM/YY HH24:MI:SS\') as time_out,inside,carrier, trash_types.wserver_id as trash_type'
    request += ',trash_cats.wserver_id as trash_cat, notes, operator, checked'
    request += ',(SELECT name FROM auto_models INNER JOIN auto ON (auto_models.id = auto.auto_model) WHERE records.car_number=auto.car_number LIMIT 1)'
    request += ', disputs.alerts'
    comm = "SELECT {} FROM {} " \
           "LEFT JOIN disputs ON (disputs.records_id = records.id) " \
           "LEFT JOIN trash_cats ON (records.trash_cat = trash_cats.id) " \
           "LEFT JOIN trash_types ON (records.trash_type = trash_types.id) " \
           "WHERE NOT (wserver_get is not null) and time_in > '14.11.2020' and not tara is null LIMIT 15".format(
        request, s.records_table)
    records, column_names = get_records_columns(sqlshell, comm)
    records = expand_reports_list(records)
    column_names = expand_column_names(column_names)
    return records, column_names


def expand_reports_list(records):
    """ Расширить данные передаваемые на WServer фотографиями"""
    new_records = []
    for rec in records:
        try:
            rec = list(rec)
            record_id = str(rec[0])
            photo_in_data = get_photodata(record_id + 'IN.jpg')
            photo_out_data = get_photodata(record_id + 'OUT.jpg')
            rec += [photo_in_data, photo_out_data]
            new_records.append(rec)
        except:
            print('Не удалось сохранить фото!')
            print(format_exc())
    return new_records


def get_photodata(photoname):
    """ Извлечь из фото последовательность байтов в кодировке base-64 """
    print('Попытка достать', photoname)
    full_name = os.sep.join((s.pics_folder, photoname))
    if not os.path.exists(full_name):
        full_name = os.sep.join((s.pics_folder, 'not_found.jpg'))
    with open(full_name, 'rb') as fobj:
        photodata = str(base64.b64encode(fobj.read()))
    return photodata


def expand_column_names(column_names):
    """ Расширить существующие поля полями photo_in & photo_out"""
    column_names = list(column_names)
    column_names += ['photo_in', 'photo_out']
    return column_names
