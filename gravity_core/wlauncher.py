from gravity_core.wlistener import WListener
from gravity_core.wengine import WEngine
from gravity_core.wsqluse_sub import WChecker
import socket
from gravity_core import wsettings as s
from gravity_core import wbuh
from time import sleep
from traceback import format_exc
from gravity_core.wftpsender import WSender
from gravity_core import support_funcs
from gravity_core.wlogger import logger
from gravity_core.functions.skud_funcs import make_connection


class Launcher:
    """ Класс для запуска Watchman-core"""

    def __init__(self):
        self.skud_conn_fault_sent = False

    def connect_skud(self, socket):
        while True:
            try:
                print('Подключение к контролеру скуд')
                response = make_connection(socket, s.contr_ip, s.contr_port)
                print('\tСтатус подключения к контроллеру СКУД:', response)
                break
            except ConnectionRefusedError:
                print('Контроллер СКУД недоступен... Переподключение.')
                logger.error('Контроллер СКУД недоступен!')
                sleep(1)
                if not self.skud_conn_fault_sent:
                    sleep(2)
                    self.skud_conn_fault_sent = True

    def _start(self):
            print('\nЗапуск Watchman CORE.')
            self.sock = socket.socket()
            self.connect_skud(self.sock)
            sql_shell = WChecker(s.db_name, s.db_user, s.db_pass, s.db_location, debug=s.SQLSHELL_DEBUG)
            apis = WListener(logger=logger)
            ftp_gate = WSender(s.newFtp_ip, s.newFtp_login, s.newFtp_pw)
            if s.IMPORT_FTP:
                bi = wbuh.BuhIntegration(sql_shell, ftp_gate)
                support_funcs.start_1c_data_importing(bi)
            self.gravity_core = WEngine(sql_shell, ftp_gate, apis, self.sock, logger=logger)
            try:
                self.gravity_core.work()
            except:
                logger.error('Ошибка в работе оператора!')
                logger.error(format_exc())


launcher = Launcher()
launcher._start()
