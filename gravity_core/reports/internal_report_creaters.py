""" Модуль с конструкторами внутренних(1С) отчетов  в форматах TXT, XML, XML EXT """
from gravity_core import wsettings as s
from datetime import datetime
from gravity_core.reports import internal_reports_funcs as rf
import xml.etree.ElementTree as xmlE


def reports_creator_core(sqlshell):
    """ Сформировать отчеты за период
    От (start_date)"""
    start_date = rf.get_last_ftp_export_date(sqlshell)
    # Запустить конструкторы отчетов
    saveDbXMLext(sqlshell, filename=s.rfid_logs_1c_xml_ext, tablename=s.book, start_date=start_date)


def get_report_date_interval(sqlshell):
    # Вернуть список строк в виде %Y-%m-%d с даты, указанной в бд по сегодняшний день
    start_date = rf.get_last_ftp_export_date(sqlshell)
    end_date = datetime.now()
    # Получить все дни за этот промежуток в виде datetime объектов
    days = rf.get_days_between(start_date, end_date)
    # Отформатировать интервал в Year-month-day формат
    formated_dates = [day.strftime('%Y-%m-%d') for day in days]
    return formated_dates


def saveDbTxt(wsqlshell, start_date, filename, tablename='records'):
    data = rf.get_records(wsqlshell, start_date, tablename=tablename)
    # Заполнить текстовый файл
    filename = open(filename, 'w', encoding='cp1251')
    tid = 'TID | ' + str(datetime.now())
    filename.write(tid)
    filename.write('\n')
    for stringname in data:
        strname = 'Events | ' + str(stringname)
        strname = strname.replace('(', '')
        strname = strname.replace(')', '')
        strlist = strname.split(',')
        carmodel = determineCarModel(allCarsDict, stringname[1])
        if carmodel == None:
            carmodel = 'Модель не опознана'
        strname += ', ' + carmodel
        filename.write(strname)
        filename.write('\n')
    print('Сохранение отчета для 1с завершено')
    filename.close()


def saveDbXML(wsqlshell, start_date, filename, tablename='records'):
    """ Сохранить отчет от start_date """
    data = rf.get_records(wsqlshell, start_date, tablename=tablename)
    root = xmlE.Element('uploads')
    root.set('TID', str(datetime.now().strftime("%d/%m/%y %H:%M:%S")))
    root.set("Poligon", "1")
    upload = xmlE.SubElement(root, 'upload')
    upload_name = xmlE.SubElement(upload, 'upload_name')
    upload_name.text = 'Date after ' + str(start_date)
    for stringname in data:
        appt = xmlE.SubElement(upload, "appointment")
        type = xmlE.SubElement(appt, 'type')
        type.text = str("events")
        id = xmlE.SubElement(appt, 'id')
        id.text = str(stringname[0])
        car_number = xmlE.SubElement(appt, 'car_number')
        car_number.text = str(stringname[1])
        brutto = xmlE.SubElement(appt, 'brutto')
        brutto.text = str(stringname[2])
        tara = xmlE.SubElement(appt, 'tara')
        tara.text = str(stringname[3])
        cargo = xmlE.SubElement(appt, 'cargo')
        cargo.text = str(stringname[4])
        date_in = xmlE.SubElement(appt, 'date_in')
        date_in.text = str(stringname[5])
        date_out = xmlE.SubElement(appt, 'date_out')
        date_out.text = str(stringname[6])
        inside = xmlE.SubElement(appt, 'inside')
        inside.text = str(stringname[7])
        alerts = xmlE.SubElement(appt, 'alerts')
        alerts.text = str(stringname[8])
        carrier = xmlE.SubElement(appt, 'carrier')
        carrier.text = str(stringname[9])
        trash_type = xmlE.SubElement(appt, 'trash_type')
        trash_type.text = str(stringname[10])
        trash_cat = xmlE.SubElement(appt, 'trash_cat')
        trash_cat.text = str(stringname[11])
        notes = xmlE.SubElement(appt, 'notes')
        notes.text = str(stringname[12])
        operator = xmlE.SubElement(appt, 'operator')
        operator.text = str(stringname[13])
        checked = xmlE.SubElement(appt, 'checked')
        checked.text = str(stringname[14])
        tara_state = xmlE.SubElement(appt, 'tara_state')
        tara_state.text = str(stringname[15])
        brutto_state = xmlE.SubElement(appt, 'brutto_state')
        brutto_state.text = str(stringname[16])
        carmodel = xmlE.SubElement(appt, 'carmodel')
        carmodel.text = str(determineCarModel(allCarsDict, stringname[1]))
    tree = xmlE.ElementTree(root)
    with open(filename, "wb") as fn:
        tree.write(fn, encoding="cp1251")


def saveDbXMLext(wsqlshell, start_date, filename, tablename='records'):
    '''Save database to XML file'''
    data = rf.get_records(wsqlshell, start_date, tablename=tablename)   # здесть тоже есть для изменения
    root = xmlE.Element('uploads')
    root.set('TID', str(datetime.now().strftime("%d/%m/%y %H:%M:%S")))
    root.set("Poligon", "1")
    upload = xmlE.SubElement(root, 'upload')
    upload_name = xmlE.SubElement(upload, 'upload_name')
    upload_name.text = 'Date after ' + str(start_date)
    request = 'SELECT id, id_1c, full_name , inn from clients '
    carrier_data = wsqlshell.try_execute_get(request)
    request = 'select name, id , id from trash_types'
    trash_t = wsqlshell.try_execute_get(request)
    request = 'select cat_name, id , id from trash_cats '
    trash_c = wsqlshell.try_execute_get(request)
    request = 'select username, id  from users '
    operator_r = wsqlshell.try_execute_get(request)
    request = 'select id, car_number, auto_model  from auto '
    auto = wsqlshell.try_execute_get(request)
    request = 'select id, name  from auto_brands '
    auto_b = wsqlshell.try_execute_get(request)
    request = 'select id, name, brand  from auto_models '
    auto_m = wsqlshell.try_execute_get(request)
    for stringname in data:
        print('Работа с {}'.format(stringname))
        appt = xmlE.SubElement(upload, "appointment")
        type = xmlE.SubElement(appt, 'type')
        type.text = str("events")
        id = xmlE.SubElement(appt, 'id')
        id.text = str(stringname[0])
        car_number = xmlE.SubElement(appt, 'car_number')
        # для авто по ид из таблицы auto
        # autos = [row for row in auto if str(stringname[1]) == row[0]] # разкоментить
        # if not auto:                                                  # разкоментить
        #     car_number.text = str(autos[0][1])                        # разкоментить
        car_number.text = str(stringname[1])                            # закомментировать
        brutto = xmlE.SubElement(appt, 'brutto')
        brutto.text = str(stringname[2])
        tara = xmlE.SubElement(appt, 'tara')
        tara.text = str(stringname[3])
        cargo = xmlE.SubElement(appt, 'cargo')
        cargo.text = str(stringname[4])
        date_in = xmlE.SubElement(appt, 'date_in')
        date_in.text = str(stringname[5])
        date_out = xmlE.SubElement(appt, 'date_out')
        date_out.text = str(stringname[6])
        inside = xmlE.SubElement(appt, 'inside')
        inside.text = str(stringname[7])
        alerts = xmlE.SubElement(appt, 'alerts')
        alerts.text = str(stringname[8])
        carrier = xmlE.SubElement(appt, 'carrier')
        if stringname[9] is not None:
            x = [row for row in carrier_data if int(stringname[9]) == row[0]]
            carrier_data_id = xmlE.SubElement(carrier, 'id')
            carrier_data_id.text = str(x[0][0])
            carrier_data_id_1c = xmlE.SubElement(carrier, 'id_1c')
            carrier_data_id_1c.text = str(x[0][1])
            carrier_data_full_name = xmlE.SubElement(carrier, 'full_name')
            carrier_data_full_name.text = str(x[0][2])
            carrier_data_inn = xmlE.SubElement(carrier, 'inn')
            carrier_data_inn.text = str(x[0][3])
        else:
            carrier.text = str(stringname[9])
        trash_type = xmlE.SubElement(appt, 'trash_type')
        if stringname[10] is not None:
            y = [row for row in trash_t if int(stringname[10]) == row[2]]
            # print(y)
            trash_type_name = xmlE.SubElement(trash_type, 'name')
            trash_type_name.text = str(y[0][0])
            trash_type_id = xmlE.SubElement(trash_type, 'id')
            trash_type_id.text = str(y[0][1])
            trash_type_type_id = xmlE.SubElement(trash_type, 'type_id')
            trash_type_type_id.text = str(y[0][2])
        else:
            trash_type.text = str(stringname[10])
        trash_cat = xmlE.SubElement(appt, 'trash_cat')
        if stringname[11] is not None:
            z = [row for row in trash_c if int(stringname[11]) == row[1]]
            # print(z)
            trash_cat_name = xmlE.SubElement(trash_cat, 'name')
            trash_cat_name.text = str(z[0][0])
            trash_cat_id = xmlE.SubElement(trash_cat, 'id')
            trash_cat_id.text = str(z[0][1])
            trash_cat_cat_id = xmlE.SubElement(trash_cat, 'cat_id')
            trash_cat_cat_id.text = str(z[0][2])
        else:
            trash_cat.text = str(stringname[11])
        notes = xmlE.SubElement(appt, 'notes')
        notes.text = str(stringname[12])
        operator = xmlE.SubElement(appt, 'operator')
        if stringname[13] is not None:
            w = [row for row in operator_r if int(stringname[13]) == row[1]]
            # print(w)
            operator_username = xmlE.SubElement(operator, 'username')
            operator_username.text = str(w[0][0])
            operator_id = xmlE.SubElement(operator, 'id')
            operator_id.text = str(w[0][1])
        else:
            operator.text = str(stringname[13])
        checked = xmlE.SubElement(appt, 'checked')
        checked.text = str(stringname[14])
        tara_state = xmlE.SubElement(appt, 'tara_state')
        tara_state.text = str(stringname[15])
        brutto_state = xmlE.SubElement(appt, 'brutto_state')
        brutto_state.text = str(stringname[16])
        autos = [row for row in auto if str(stringname[1]) == row[1]]   # Закоментировать
        # autos = [row for row in auto if str(stringname[1]) == row[0]] # разкоменировать
        # print(autos)
        if not autos:
            models = [row for row in auto_m if int(autos[0][2]) == row[0]]
            brands = [row for row in auto_b if int(models[0][2]) == row[0]]
            carbrand = xmlE.SubElement(appt, 'carbrand')
            carbrand.text = str(brands[0][1])
            carmodel = xmlE.SubElement(appt, 'carmodel')
            carmodel.text = str(models[0][1])
        # carmodel.text = str(determineCarModel(allCarsDict, stringname[1]))
    tree = xmlE.ElementTree(root)
    # , encoding = 'cp1251'
    #with open(s.rfid_logs_1c_xml_ext, "wb") as fn:
    #    tree.write(fn, encoding="cp1251")
    # fn.write(xmlE.tostring(tree).decode("utf-8"))
    #with open(s.rfid_logs_1c_xml_ext_1pol, "wb") as fn:
    #    tree.write(fn, encoding="cp1251")
    # fn.write(xmlE.tostring(tree).decode("utf-8"))
    with open(filename, "wb") as fn:
        tree.write(fn, encoding="cp1251")

def determineCarModel(allcars, carnum):
    try:
        carmodel = allcars[carnum]
    except KeyError:
        carmodel = 'Модель не опознана'
    return carmodel


def get_frmt_db_date(self, date):
    date = date.split(' ')[0]
    full = date.replace('.', '-')
    return full