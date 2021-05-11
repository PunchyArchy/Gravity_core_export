from gravity_core import wsettings as s
from wsqluse.wsqluse import Wsqluse
from datetime import datetime
from traceback import format_exc
from gravity_core.functions import alert_funcs


class WChecker(Wsqluse):
    """ Подкласс WSqluse, хранящий специфичные для AR запросы в БД"""

    def __init__(self, dbname, user, password, host, debug=False):
        Wsqluse.__init__(self, dbname, user, password, host, debug=debug)

    def check_car_choose_mode(self, alerts, choose_mode, car_number, course):
        # Проверить, как была выбрана машина (вручную/автоматоически)
        rfid = self.get_rfid_by_carnum(car_number)[0][0]
        alerts = alert_funcs.check_car_choose_mode(rfid, alerts, choose_mode, car_number, course)
        return alerts

    def get_rfid_by_carnum(self, carnum):
        """ Вернуть RFID-номер машины по его гос.номеру """
        command = "SELECT rfid FROM auto WHERE car_number='{}'".format(carnum)
        response = self.try_execute_get(command)
        return response

    def check_car(self, cargo, alerts):
        alerts = alert_funcs.cargo_null(cargo, alerts)
        return alerts

    def check_ph_state(self, ph_els_dict, alerts, polomka_state, dlinnomer_state):
        alerts = alert_funcs.check_ph_state(ph_els_dict, alerts, polomka_state, dlinnomer_state)
        return alerts

    def fast_car(self, carnum, alerts):
        # Проверить, не слишком ли быстро вернулась машина, если да - дополнить алерт кодом из wsettings и вернуть
        print('\nИнициирована проверка на FastCar')
        timenow = datetime.now()
        check = s.alerts_description['fast_car']
        command = "SELECT le.date from last_events le INNER JOIN auto a ON (le.car_id=a.id) " \
                  "where a.car_number='{}'".format(carnum)
        try:
            last_visit_date = self.try_execute_get(command)[0][0]
            alerts = alert_funcs.check_fast_car(last_visit_date, timenow,  alerts)
        except:
            print('\tОшибка при проверке заезда')
            print(format_exc())
        return alerts

    def check_car_inside(self, carnum, tablename):
        '''Проверяет находится ли машина на территории предприятия'''
        # self.check_presence(carnum, tablename, column)
        response = self.try_execute_get("select * from {} where car_number='{}' and inside='yes'".format(tablename, carnum))
        if len(response) > 0:
            return True

    def get_last_id(self, tablename):
        # Вернуть максимальный ID из таблицы tablename
        command = "select max(id) from {}".format(tablename)
        max_id = self.try_execute_get(command)
        return max_id

    def get_last_visit(self, tablename, ident, value):
        # Вернуть строку с последней записью из таблицы tablename, где выполняется условие ident, сортируется по value
        command = 'SELECT * FROM {} where {} ORDER BY {} DESC LIMIT 1'.format(tablename, ident, value)
        record = self.try_execute_get(command)
        return record

    def add_alerts(self, alerts, rec_id):
        '''Добавляет строку в таблицу disputs, где указываются данные об инциденте'''
        self.show_print('\n###Добавляем новые алерты к записи###')
        self.show_print('\talerts -', alerts)
        if len(alerts) > 0:
            timenow = datetime.now()
            command = "insert into {} ".format(s.disputs_table)
            command += "(date, records_id, alerts) "
            command += "values ('{}', {}, '{}') ".format(timenow, rec_id, alerts)
            command += "on conflict (records_id) do update "
            command += "set alerts = disputs.alerts || '{}'".format(alerts)
            self.try_execute(command)

    def updLastEvents(self, carnum, carrier, trash_type, trash_cat, timenow):
        self.show_print('\nОбновление таблицы lastEvents')
        carId = "select id from auto where car_number='{}' LIMIT 1".format(carnum)
        comm = 'insert into {} '.format(s.last_events_table)
        comm += '(car_id, carrier, trash_type, trash_cat, date) '
        comm += "values (({}),{},{},{},'{}') ".format(carId, carrier, trash_type, trash_cat, timenow)
        comm += 'on conflict (car_id) do update '
        comm += "set carrier={}, trash_cat={}, trash_type={}, date='{}'".format(carrier, trash_cat, trash_type, timenow)
        self.try_execute(comm)


    def upd_old_num(self, old_carnum, new_carnum):
        # Обновляет старый номер на новый
        command = "UPDATE {} SET car_number='{}' WHERE car_number='{}'".format(s.auto, new_carnum, old_carnum)
        self.try_execute(command)

    def check_access(self, rfid):
        '''Проверяет, разрешается ли машине въезд'''
        command = "SELECT rfid FROM {} WHERE rfid='{}' and active=True".format(s.auto, rfid)
        response = self.try_execute_get(command)
        if len(response) > 0:
            return True

    def create_str(self, tablename, template, values):
        """Создает новую строку в БД, получает кортеж-шаблон, и кортеж
        значений, а так-же возвращает id записи"""
        response = self.try_execute('insert into {} {} values {}'.format(tablename,
                                                                         template, values))
        rec_id = response['info'][0][0]
        return rec_id

