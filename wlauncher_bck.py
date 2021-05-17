from gravity_core.wlistener import WListener
from gravity_core.wengine import WEngine
from gravity_core.wsqluse_sub import WChecker
import socket
from gravity_core import wsettings as s
from gravity_core.wlogger import logger
from gravity_core import wbuh
from time import sleep
from traceback import format_exc
from gravity_core.wftpsender import WSender
from gravity_core import support_funcs
import threading




class Launcher:
    """ Класс для запуска Watchman-core"""

    def __init__(self):
        self.skud_conn_fault_sent = False

    def connect_skud(self, socket):
        while True:
            try:
                print('Подключение к контролеру скуд')
                socket.connect((s.contr_ip, s.contr_port))
                socket.send(b'"LOGIN" 1.8 "Administrator" ""\r\n')
                print('\tСтатус подключения к контроллеру СКУД:', socket.recv(1024))
                break
            except ConnectionRefusedError:
                print('Контроллер СКУД недоступен... Переподключение.')
                logger.error('Контроллер СКУД недоступен!')
                sleep(1)
                if not self.skud_conn_fault_sent:
                    sleep(2)
                    self.skud_conn_fault_sent = True

    def _start(self):
        #while True:
            print('\nЗапуск Watchman CORE.')
            self.sock = socket.socket()
            self.connect_skud(self.sock)
            sql_shell = WChecker(s.db_name, s.db_user, s.db_pass, s.db_location, debug=s.SQLSHELL_DEBUG)
            apis = WListener(logger=logger)
            if s.IMPORT_FTP:
                ftp_gate = WSender(s.newFtp_ip, s.newFtp_login, s.newFtp_pw)
                bi = wbuh.BuhIntegration(sql_shell, ftp_gate)
                threading.Thread(target=support_funcs.start_1c_data_importing, args=(bi,)).start()
            else:
                ftp_gate = None
            self.gravity_core = WEngine(sql_shell, ftp_gate, apis, self.sock, logger)
            try:
                self.gravity_core.work()
            except:
                print(format_exc())
                logger.error('Ошибка в работе оператора!')
                logger.error(format_exc())


launcher = Launcher()
launcher._start()
