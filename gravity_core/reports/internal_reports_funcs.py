""" Хранит все функции для работы с внутренними (1С) отчетами"""
import datetime
import ftplib
from gravity_core import wsettings
import schedule
from time import sleep
from gravity_core.functions.tryexceptdecorator import *
import datetime
from gravity_core.reports import internal_report_creaters
from wsqluse.wsqluse import Wsqluse
import gravity_core.wsettings as s
import os



def schedule_reports_sending():
    """ Аналог cron. Планирует отправку отчетов по временам, заданным в s.reports_time """
    form_send_reports()
    for time in wsettings.reports_time:
        schedule.every().day.at(time).do(form_send_reports)
    while True:
        schedule.run_pending()
        sleep(1)


@try_except_decorator('Отправка отчетов')
def form_send_reports():
    sqlshell = Wsqluse(wsettings.db_name, wsettings.db_user, wsettings.db_pass, '192.168.100.109')
    internal_report_creaters.reports_creator_core(sqlshell=sqlshell)
    # Отправка
    send_files(wsettings.newFtp_ip, wsettings.newFtp_login, wsettings.newFtp_pw, s.rfid_logs_1c_xml_ext)
    print('\nОтправка отчетов на 1С завершена')


def form_send_reports_cycle(sqlshell, interval):
    """ Цикл формирования и отправки актов каждые interval секунд """
    while True:
        # Формирование
        form_send_reports_cycle(sqlshell)
        sleep(interval)


def get_last_ftp_export_date(sqlshell):
    """ Узнать последнюю дату выгрузки данных на FTP"""
    command = "SELECT date FROM exchange_date WHERE info_type=' Запрос выгрузки с весовой '"
    last_export_date = sqlshell.try_execute_get(command)[0][0]
    last_export_date = last_export_date.replace(tzinfo=None)
    return last_export_date


def get_days_between(start_date, end_date):
    """Получет стартовую и конечную даты в виде объектов datetime,
    возвращает все даты в этом интервале виде списка объектов datetime"""
    _timedelta = end_date - start_date
    daysBetween = _timedelta.days + 1
    date_list = [end_date - datetime.timedelta(days=x) for x in range(daysBetween)]
    return date_list


def send_files(host, ftp_user, ftp_password, *filenames):
    """ Передать файлы на FTP server """
    con = ftplib.FTP(host, ftp_user, ftp_password)
    con.set_pasv(False)
    con.sendcmd('PASV')
    # Открываем файл для передачи в бинарном режиме
    con.cwd('/ftp')
    for filename in filenames:
        # filename = filename.split('/')[-1]
        f = open(filename, "rb")
        # Передаем файл на сервер
        filename = filename.split(os.sep)[-1]
        send = con.storbinary("STOR " + filename, f)
    # Закрываем FTP соединение
    con.close()


def get_records(sqlshell, start_date, tablename='records'):
    # Получить записи
    request = 'id,car_number,brutto,tara,cargo, to_char("time_in",\'DD/MM/YY HH24:MI:SS\')' # закоментировать
    # request = 'id,auto,brutto,tara,cargo, to_char("time_in",\'DD/MM/YY HH24:MI:SS\')'     # разкоментировать
    request += ',to_char("time_out",\'DD/MM/YY HH24:MI:SS\'),inside,alerts,carrier,trash_type'
    request += ',trash_cat,notes,operator,checked,tara_state,brutto_state'
    comm = "select {} from {} where time_in >= '{}'".format(request, tablename, start_date)
    data = sqlshell.try_execute_get(comm)
    return data 