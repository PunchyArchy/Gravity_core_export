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
        """ Запустить основной цикл работы """
        print('\nЗапуск Watchman CORE.')
        # Подключиться к контроллеру СКУД
        if s.TEST_MODE:                                       # Если тестовый режим - создать эмулятор контроллера скуд
            from gravity_core.tools.test_mode import SkudTestSocket
            self.sock = SkudTestSocket()
        else:
            self.sock = socket.socket()
        self.connect_skud(self.sock)                                                 # Подключиться к контроллеру скуд
        # Создать фреймворк для работы с БД и API для внешних систем (СМ)
        sql_shell = WChecker(s.db_name, s.db_user, s.db_pass, s.db_location, debug=s.SQLSHELL_DEBUG)  # Создать sqlshell
        apis = WListener(logger=logger)                                              # Подключить модуль API
        # Интеграция с 1С через FTP
        if s.IMPORT_FTP:                                   # Если есть интеграция с 1с через FTP
            ftp_gate = WSender(s.newFtp_ip, s.newFtp_login, s.newFtp_pw)
            bi = wbuh.BuhIntegration(sql_shell, ftp_gate)
            support_funcs.start_1c_data_importing(bi)
        else:
            ftp_gate = None
        # Создать ядро и запустить его
        self.gravity_core = WEngine(sql_shell, ftp_gate, apis, self.sock, logger=logger)
        try:
            self.gravity_core.work()
        except:
            logger.error('Ошибка в работе оператора!')
            logger.error(format_exc())


launcher = Launcher()
launcher._start()
