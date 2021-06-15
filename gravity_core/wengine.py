import os
from datetime import datetime
import threading
from gravity_core import wsettings as s
from whikoperator.main import Wpicoperator
from gravity_core.wtools import *
from gravity_core.functions.tryexceptdecorator import *
from gravity_core import support_funcs as sup_funcs
from gravity_core.reports import internal_reports_funcs as rep_funcs
from gravity_core.reports import signall_reports_funcs as sig_funcs
from weightsplitter.main import WeightSplitter
from gravity_core.functions import wserver_interaction
from time import sleep
from gravity_core import health_monitor
from gravity_core.functions.skud_funcs import *
from gravity_core_api.main import GCSE
from gravity_core.functions import duo_functions
from gravity_core.functions.asu_routes import check_if_car_tko, get_tko_id, check_asu_routes


# from weightsplitter.main import WeightSplitter


class WEngine:
    """ Основное ядро программы"""

    def __init__(self, sqlshell, ftp_gate, wlistener, skud_sock, logger):
        # Создание экземпляров
        self.logger = logger
        self.wserver_connected = False
        self.debug = s.GENERAL_DEBUG
        self.found_errors = []
        self.sqlshell = sqlshell
        self.wlistener = wlistener
        self.sock = skud_sock
        self.ftp_gate = ftp_gate
        self.status = 'Готов'
        if not s.IMPORT_FTP:
            self.try_ftp_connect()
        if not s.TEST_MODE:
            self.cam = Wpicoperator(s.cam_ip, s.cam_login, s.cam_pw, s.pics_folder, s.fpath_file, auth_method='Digest')
            threading.Thread(target=self.make_cps_connection, args=()).start()
        # Параметры по умолчанию #
        self.poligon_id = 0
        self.alerts = ''
        self.lastVisit = {}
        self.lrs = datetime(1997, 8, 24)
        self.lrs2 = datetime(1997, 8, 24)
        self.weightlist = []
        self.currentProtocolId = ''
        self.contr_mes = b'empty contr mes'
        self.addInfo = {'status': 'none', 'notes': 'none', 'protocol': 'none', 'course': 'none'}
        self.all_wclients = []
        self.serving_start()
        self.phNotBreach = False
        self.contr_stream = []
        self.polomka = 0
        self.dlinnomer = 0
        self.ph_els = {'3': '30', '4': '30'}
        self.polygon_name = 'unknown'

    def try_ftp_connect(self):
        try:
            self.ftp_gate.make_connection()
        except:
            self.send_error('Нет доступа к FTP-серверу.')

    def create_api(self):
        """ Инициировать единый API endpoint"""
        self.api_endpoind = GCSE('0.0.0.0', s.wserver_reciever_port, self.sqlshell, self)
        self.api_endpoind.launch_mainloop()

    def make_cps_connection(self):
        """ Подключиться к серверу раздачи весов"""
        while True:
            try:
                self.cps = WeightSplitter(s.scale_splitter_ip, s.scale_splitter_port, port_name=s.ws_port, terminal_name=s.ws_name, debug=s.WS_DEBUG)
                self.cps.start()
                health_monitor.change_status('Весовой терминал', True, 'Весовой терминал функционирует нормально')
                break
            except:
                self.operate_exception('Не удалось подключиться к модулю CPS!')
                health_monitor.change_status('Весовой терминал', False, 'Не удалось подключиться к весовому терминалу')
                sleep(5)

    def wserver_reconnecter(self):
        while True:
            if not self.wserver_connected:
                wserver_client = wserver_interaction.create_wserver_connection()
                self.all_wclients.append(wserver_client)
                if wserver_client:
                    self.poligon_id = wserver_interaction.auth_me(wserver_client)
                    self.wserver_connected = True
                    self.send_act()
            else:
                pass
            self.show_notification("[WSERVER_RECONNECTER]. Connect status =", self.wserver_connected, debug=True)
            sleep(15)

    def operate_exception(self, tag=''):
        """Вызывается для перехвата исключений. Показывает в потоке вывода задаваемый тег,
		текст ошибки, а так-же логгирует текст ошибки"""
        self.show_notification(tag)
        self.show_notification(format_exc())
        self.logger.error(format_exc())
        self.opl_make_record(format_exc())
        self.send_error(tag)

    def serving_start(self):
        """Запуск обслуживающих демонов"""
        self.show_notification('REPORTING. DEMONS STARTED')
        # Создать сокет для принятия выполнения SQL команд от WServer
        threading.Thread(target=self.create_api, args=()).start()
        if s.AR_DUO_MOD:
            self.connect_to_wserver_duo()
        else:
            threading.Thread(target=self.wserver_reconnecter, args=()).start()
        if not s.TEST_MODE:
            # Демон по получению весов с WeightSplitter
            threading.Thread(target=self.wlistener.scale_reciever, args=()).start()
        if s.IMPORT_FTP:
            threading.Thread(target=rep_funcs.schedule_reports_sending, args=()).start()  # Демон отправки отчетов на 1С
            rep_funcs.form_send_reports()              # Сформировать и отправить акты разово на ФТП
        # Демон запуска сокета для отправки статусов о работе Watchman-Core для CM
        threading.Thread(target=self.wlistener.statusSocket, args=()).start()
        # Запуск API для принятия обычных команд от CM (типа get_status, orup_enter и проч.)
        threading.Thread(target=self.wlistener.dispatcher, args=(
            s.cmUseInterfaceIp, s.cmUseInterfacePort, self.wlistener.executeComm,
            'API для принятия обычных команд запущен.')).start()
        # Запуск API для принятия SQL команд от СМ и выполнения их на борту
        threading.Thread(target=self.wlistener.dispatcher, args=(
            s.cmUseInterfaceIp, s.cm_sql_operator_port, self.wlistener.cm_sql_operator_loop,
            'API для принятия SQL команд запущен.')).start()
        # Задать ядро API для взаимодействия
        self.set_wlistener_core()

    def connect_to_wserver_duo(self):
        """ Подключиться к WSERVER """
        # А теперь создаем сокеты для отправки данных на WServer
        # Вернуть словарь типа {'conn_name': {'wclient': socket_obj, ... }}
        self.all_wclients = duo_functions.get_all_poligon_connections(self.sqlshell, s.pol_owners_table, s.wserver_ip,
                                                                            s.wserver_port)
        print("INITING SELF.ALL_WCLIENTS", self.all_wclients)
        # Отдать словарь на обслуживание демону
        duo_functions.launch_wconnection_serv_daemon(self.sqlshell, self.all_wclients, s.connection_status_table,
                                                           s.pol_owners_table)
        # Отправить акты
        duo_functions.send_act_by_polygon(self.all_wclients, self.sqlshell, s.connection_status_table,
                                          s.pol_owners_table)

    def set_wlistener_core(self):
        self.wlistener.set_wcore(self)

    def blockAR(self, status='Занят'):
        # Выполнить блокировку AR (начать заезд)
        self.show_notification('\nБлокировка АР')
        self.wlistener.status = status

    def unblockAR(self, status='Готов'):
        # Выополнить деблокировку AR (перейти в режим ожидания)
        self.show_notification('Разблокировка АР\n')
        self.wlistener.status = status

    def operate_external_command(self, comm):
        """ Обработка каждой команды, поступающей на API """
        command, info = self.comm_parse(comm)
        if command == 'start_car_protocol':
            self.cic_start_car_protocol(info)
        elif command == 'cm_user_auth':
            self.installUserCfg(self.wlistener.cm_logged_username, self.wlistener.cm_logged_userid)
        elif command == 'gate_manual_control':
            self.operate_gate_manual_control(info)
        elif command == 'change_record':
            self.change_record(info)
        elif command == 'add_comm':
            self.add_comm(info)
        else:
            self.show_notification('Неизвестная комманда')
        self.unblockAR()

    def change_record(self, info):
        """ Изменить незавершенный заезд командой из СМ"""
        command = "UPDATE {} SET carrier={}, trash_type={},trash_cat={}, notes='{}' WHERE id={}".format(s.book,
                                                                                                        info['carrier'],
                                                                                                        info['trash_type'],
                                                                                                        info['trash_cat'],
                                                                                                        info['notes'],
                                                                                                        info['record_id'])
        self.sqlshell.try_execute(command)

    def add_comm(self, info):
        """ Добавить комментарий к завершенному заезду командой из СМ """
        command = "UPDATE {} set notes = notes || 'Добавочно: {}' where id={}".format(s.book, info['notes'],
                                                                                      info['record_id'])
        self.sqlshell.try_execute(command)

    def operate_gate_manual_control(self, info):
        """ Опрерирует коммандами на закрытие/открытие шлагбаумами от СМ """
        if info['operation'] == 'close':
            self.close_gate(info['gate_name'])
        elif info['operation'] == 'open':
            self.open_gate(info['gate_name'])

    def parse_cm_info(self, info):
        # Парсит данные о заезде, переданные от СМ и сохраняет в собственный словарь, дублируя данные.
        # Это необходимо для того, что если на СМ изменят какой либо передаваемый ключ, его не надо будет менять
        # везде в AR. Достаточно будет поменять его здесь.
        new_info = {}
        new_info['timenow'] = self.get_timenow()  # Добавить текущее время
        new_info['carnum'] = info['carnum']
        new_info['comm'] = info['comm']
        new_info['course'] = info['course']
        new_info['car_choose_mode'] = info['car_choose_mode']  # Данные о способе пропуска
        new_info['car_protocol'] = self.define_idtype('car_number', info['carnum'])  # Добавить данные о протоколе
        new_info['have_brutto'] = self.check_car_have_brutto(info['carnum'])  # Данные о взвешивании
        new_info['dlinnomer'] = info['dlinnomer']
        new_info['polomka'] = info['polomka']
        new_info['orup_mode'] = info['orup_mode']
        # Если это выездной ОРУП - эти данные не удастся достать
        if new_info['orup_mode'] != 'orup_short':
            new_info['operator'] = info['operator']
            new_info['carrier'] = info['carrier']
            new_info['trash_cat'] = info['trash_cat']
            new_info['trash_type'] = info['trash_type']
            new_info['old_carnum'] = info['carnum_was']
            if s.AR_DUO_MOD:
                self.polygon_name = info['polygon_object']
            if s.ASU_ROUTES:
                self.must_be_tko = info['must_be_tko']
            new_info = self.check_db_value(new_info)
        self.show_notification('\nNew_info_dict after parsing:', new_info, debug=True)
        return new_info

    def check_db_value(self, info):
        # Проверяет, везде ли взяты id как идентификаторы
        if not info['trash_cat'].isdigit():
            info['trash_cat'] = self.getKeyCommand('trash_cats', 'id', "cat_name='{}'".format(info['trash_cat']))
        if not info['trash_type'].isdigit():
            info['trash_type'] = self.getKeyCommand('trash_types', 'id', "name='{}'".format(info['trash_type']))
        if not info['operator'].isdigit():
            info['operator'] = self.getKeyCommand('users', 'id', "username='{}'".format(info['operator']))
        if not info['carrier'].isdigit():
            info['carrier'] = self.getKeyCommand('clients', 'id', "short_name='{}'".format(info['carrier']))
        return info

    def cic_start_car_protocol(self, info):
        # Работаем с командой создания/продолжения проткола, отправленной из СМ
        info = self.parse_cm_info(info)
        self.pre_any_protocol_operations(info)
        if info['have_brutto']:
            # Если машина уже взвесила брутто
            self.operate_orup_exit_commands(info)
        else:
            # Если же машина первый раз въезжает на территорию
            self.pre_open_protocol_operations(info)
            self.operate_orup_enter_commands(info)

    def pre_any_protocol_operations(self, info):
        # Операции, которые необходимы быть выполнены перед началом любого протокола
        self.blockAR()
        self.opl_create_file(info['carnum'])
        self.choose_mode = info['car_choose_mode']
        self.define_if_polomka_or_dlinnomer(info)
        self.lastVisit[info['carnum']] = info['timenow']
        anim_info = self.get_anim_info(info['course'], info['car_protocol'], 'start_pos')
        # ФРИЗ ЗДЕСЬ ERROR
        self.updAddInfo(status='Начало взвешивания', carnum=info['carnum'], face=anim_info['face'],
                        pos=anim_info['pos'])
        self.alerts = ''

    def pre_open_protocol_operations(self, info):
        # Операции, которые необходимы быть выполнены перед началом любого стартового протокола
        if not sup_funcs.check_car_registered(self.sqlshell, info['carnum']):
            sup_funcs.register_new_car(self.sqlshell, info['carnum'])
        if info['car_choose_mode'] == 'auto':
            self.orup_num_upd(info)
        self.alerts = self.sqlshell.fast_car(info['carnum'], self.alerts)
        if s.ASU_ROUTES:
            self.alerts = check_asu_routes(self.sqlshell, s.trash_cats_table, info['trash_cat'], self.must_be_tko, self.alerts,
                                           s.alerts_description['tko_instead_other']['description'],
                                           s.alerts_description['other_instead_tko']['description'])
        self.sqlshell.updLastEvents(info['carnum'], info['carrier'], info['trash_type'], info['trash_cat'],
                                    info['timenow'])

    def pre_close_protocol_operations(self, carnum, carrier, trash_type, trash_cat, timenow):
        # Операции, которые необходимы быть выполнены перед началом любого закрывающего протокола
        pass

    def operate_orup_enter_commands(self, info):
        # Работает с коммандами, пришедшими из въездного ОРУП (инициализация протокола)
        if info['car_protocol'] == 'rfid':
            if info['course'] == 'IN':
                # Если инициируется взвешивание брутто для машины протокола rfid, приехавшей с внешней стороны
                self.entering(carnum=info['carnum'], timenow=info['timenow'], contragent=info['carrier'],
                              trashcat=info['trash_cat'], trashtype=info['trash_type'], comm=info['comm'],
                              operator=info['operator'])
            elif info['course'] == 'OUT':
                # Если инициируется взвешивание брутто для машины протокола rfid, приехавшей с внутренней стороны
                self.escaping(info['carnum'], comm=info['comm'], mode='incorrect')
        elif info['car_protocol'] == 'NEG':
            # Если протокол NEG на стадии инициации, передать функции направление, с какой стороны открывать шлагбаум
            self.neg_init_record(info['carnum'], info['timenow'], info['trash_cat'], info['trash_type'],
                                 info['carrier'],
                                 info['comm'], info['operator'], info['course'])
        elif info['car_protocol'] == 'tails':
            # Если иницируется взвешивание брутто для машины протокола Tails
            self.tails_group_init_record(info['carnum'], info['timenow'], info['trash_cat'], info['trash_type'],
                                         info['carrier'], info['comm'], info['operator'], info['course'])
        elif info['car_protocol'] == 'across':
            self.across_group(info['carnum'], info['timenow'], info['course'])

    def operate_orup_exit_commands(self, info):
        # Работает с коммандами, пришедшими из выездного ОРУП
        carnum = info['carnum']
        if type(carnum) == tuple:
            carnum = carnum[0]
        if info['car_protocol'] == 'rfid':
            if info['course'] == 'IN':
                self.close_open_records(carnum, info)
            elif info['course'] == 'OUT':
                self.escaping(carnum, comm=info['comm'], mode='correct')
        elif info['car_protocol'] == 'NEG':
            # Если протокол NEG на стадии закрытия, передать функции направление, с какой стороны открывать шлагбаум
            self.neg_close_record(carnum, info['timenow'], info['comm'], info['course'])
        elif info['car_protocol'] == 'tails':
            self.tails_group_close_record(carnum, info['timenow'], info['comm'], info['course'])
        elif info['car_protocol'] == 'across':
            self.across_group(carnum, info['timenow'], info['course'])

    def orup_num_upd(self, info):
        print('\n[func]orup_num_upd. Locals:', locals())
        print('Проверяем, изменили ли номер с ОРУП.')
        # Проверяет, изменили ли номер с ОРУП
        if self.check_if_num_changed(info):
            print('\tНомер был изменен. Обновляем базу...')
            # Если да, обновляет базу
            self.sqlshell.upd_old_num(info['old_carnum'], info['carnum'])
            # Ну и возвращает для этого заезда уже новый номер
            return info['carnum']
        else:
            print('\tНомер не был изменен.')
            return info['old_carnum']

    def check_if_num_changed(self, info):
        # Проверяет, совпадает ли старый номер с новым
        if info['old_carnum'] != info['carnum'] and info['car_protocol'] != 'rfid' and info[
            'car_choose_mode'] != 'manual':
            return True

    def define_if_polomka_or_dlinnomer(self, info):
        # Определяет, были ли выбран для заезда спец.протокол "Длинномер" или "Поломка"
        self.dlinnomer = info['dlinnomer']
        self.polomka = info['polomka']

    def comm_parse(self, comm):
        self.show_notification('''Парсит данные, приходящие в виде команды''')
        for command, info in comm.items():
            return command.strip(), info

    def catching_weight(self, course, id_type, only_breach=True):
        """ Взвешивание по стабилизации веса на весовой платформе"""
        # Взять последний вес
        weight = self.wlistener.smlist[-1]
        # Ждать, пока пересекут фотоэлементы (only_breach значит, что даже освобождения не нужно)
        self.check_ph_release(course, only_breach=only_breach)
        # Получить данные об анимации на весах (в какую сторону направлена машина)
        anim_info = self.get_anim_info(course, id_type, 'middle_pos')
        self.updAddInfo(status='Успешно. Взвешивание...', pos=anim_info['pos'], face=anim_info['face'])
        # Взять последние s.stable_scaling_wait_time (5 обычно) весов из потока весов
        weight_slice = self.wlistener.smlist[:-s.stable_scaling_wait_time]
        # Повторять цикл, пока значения не устаканятся
        while not self.check_weight_stable(weight_slice) and int(weight) < int(s.stable_win_weight):
            sleep(1)
            weight_slice = self.wlistener.smlist[:-s.stable_scaling_wait_time]
            self.show_notification('Catching weight:', weight_slice)
        # Взять последний вес и вернуть его
        weight = weight_slice[-1]
        self.updAddInfo(status='Вес взят.', notes=weight)
        return weight

    def check_weight_stable(self, weight_slice):
        # Проверить список, все ли элементы равны друг другу в пределах admitting_spikes (50 кг обычно)
        weight_slice = iter(weight_slice)
        # print("CHECKING")
        try:
            first = next(weight_slice)
        except StopIteration:
            return True
        return all(int(first) in range(int(rest) - s.admitting_spikes, int(rest) + s.admitting_spikes) for rest in
                   weight_slice)

    def get_timenow(self):
        '''Возвращает отформатированную, читабельную дату'''
        today = datetime.today()
        frmt = today.strftime('%Y.%m.%d %H:%M:%S')
        return datetime.now()

    def photo_scaling(self, course, id_type, only_breach=False):
        """ Взвешивание """
        try:
            # Дождаться пересечения фотоэлементов
            weight = self.catching_weight(course, id_type, only_breach=only_breach)
            health_monitor.change_status('Фотоэлементы', True, 'Подключение стабильно')
        except PhNotBreach:
            # Если фотоэлемент не был пересечен, все равно вернуть вес, который сейчас показывают весы
            weight = self.wlistener.smlist[-1]
            self.phNotBreach = True
            health_monitor.change_status('Фотоэлементы', False, 'Есть подозрение что не работают')
        # Проверить не заблокированы ли фотоэлементы
        self.show_notification('Положение фотоэлементов -', self.ph_els)
        self.alerts = self.sqlshell.check_ph_state(self.ph_els, self.alerts, self.polomka, self.dlinnomer)
        print('Photo scaling backing:', weight)
        return weight

    def str_check(self, course, id_type):
        """ Старый метод взвешивания. Взвешивает по факту освобождения линии фотоэлементов после пересчения с
        ожидаемой стороны и паузой в несколько секунд"""
        self.ph_count = 0
        self.show_notification('Слежение за фотоэлементами началось.')
        self.check_ph_release(course)
        self.show_notification('\nФаза-2. Ожидание', s.ph_time, 'сек.')
        anim_info = self.get_anim_info(course, id_type, 'middle_pos')
        self.updAddInfo(status='Успешно. Взвешивание...', face=anim_info['face'], pos=anim_info['pos'])
        while self.ph_count < s.ph_time:
            sleep(1)
            self.ph_count += 1
            self.add_weight()
        self.show_notification('\nФаза-3. Взятие веса.')
        weight = self.take_weight()
        self.updAddInfo(status='Вес взят.', notes=weight)
        return weight

    def check_ph_release(self, course, mode='usual', only_breach=False):
        """ Проверка пересечения фотоэлементов """
        # По умолчанию фотоэлементы свободны, ни одного события с контроллера Skud в self.contr_stream
        self.ph_els = {'3': '30', '4': '30'}
        self.contr_stream = []

        if course == 'IN':
            # Если машина въезжает, контроллировать въездной шлагбаум
            gate = 'entry'
        else:
            # Если машина выезжает, контроллировать выездной шлагбаум
            gate = 'exit'
        count = 0
        # Ожидать пересечения фотоэлементов timer секунд
        timer = s.ph_release_timer
        # Сохранить значение по умолчанию в пермененую start_time
        start_timer = timer
        # Запомнить длину списка событий с контроллера Скуд
        self.os = len(self.contr_stream)
        # Переходим в первую фазу
        self.show_notification('\nФаза-1. Ожидание пересечения фотоэлементов.')
        self.updAddInfo(status='Ожидание пересечения фотоэлементов.')
        # Пока счетчик не равно lib_time секунд (т.е. фотоэлементы освободились и не пересекались вновь в течение
        # этого времени (lib_time секунд)
        while count < s.lib_time:
            self.updAddInfo(notes='Таймер - {} сек'.format(timer))
            # Если появилось новое событие в списке событий контроллера и это событие связано с фотоэлементами
            if (self.check_if_new_contr_mess(self.os) and self.contr_stream[-1][4] == s.entry_ph_num
                    or self.check_if_new_contr_mess(self.os) and self.contr_stream[-1][4] == s.exit_ph_num):
                # Сохранить вес
                weight_on_scale = self.add_weight(mode='int')
                if self.check_course(course) and mode == 'esc':
                    # Машина пересекла линию фотоэлементов и должна съезжать с весов (взвесила тару), игнорировать вес
                    count += 1
                    timer = start_timer
                    print('c1')
                elif self.check_course(course) and self.check_car_on_scale(weight_on_scale, s.min_weight_ph_checking):
                    # Машина пересекла линию фотоэлементов и взобралась на весы (взвешивает брутто), следить за весом
                    count += 1
                    timer = start_timer
                    print('c2')
                else:
                    # Если же больше ничего не происходит (фотоэлементы пересеклись и все), ждать пока дальше
                    timer -= 1
                    print('c3')
                    if only_breach and self.check_car_on_scale(weight_on_scale, s.min_weight_ph_checking):
                        # Но если ничего и не нужно (режим только пересечение), значит все путем, вернуть функцию
                        count += 1
                        print('c4')
            else:
                # Если вообще ничего не происходит (ни одного события с фотоэлементами), крутить таймер
                count = 0
                timer -= 1
                print('c5')
            # Таймер говорит тик-так
            sleep(1)
            if timer == 0:
                # Если таймер равен нулю, значит условие не выполнено, закрыть открытый шлагбаум
                self.add_weight()
                self.gate_scale_control_mechanism(mode, gate)
                # И возбудить алерт
                raise PhNotBreach
        # Если дошло до сюда, значит условие выполнено, закрыть шлагбаум
        if only_breach:
            #mode = 'esc'
            print('c6')
        self.gate_scale_control_mechanism(mode, gate)
        print('c7')

    def check_car_on_scale(self, weight, min_weight=100):
        """ Проверяет, находится ли машина на весах, а еще смотрит, кратен ли вес 10, ибо если нет, значит
         WeightSplitter выкинул какую то ошибку, а значит пролдолжать заезд нельзя"""
        weight = abs(int(weight))
        if weight < min_weight and weight % 10 != 0:
            return False
        elif weight < min_weight and weight % 10 == 0:
            return False
        elif weight > min_weight and weight % 10 == 0:
            return True

    def check_if_new_contr_mess(self, old_state):
        # Вернуть True, если появилось новое событие в потоке слежения за фотоэлементами
        if len(self.contr_stream) > old_state:
            return True

    def check_scale_idle(self):
        # Проверить, свободны ли весы
        if self.add_weight(mode='int') < s.scale_idle_param and not s.ph_lock_state in self.ph_els.values():
            # Если весы показывают меньше определенного веса и оба фотоэлемнта деблокированы, вернуть истину
            return True

    def gate_scale_control_mechanism(self, mode, gate):
        """ Механизм контролирования закрытия стрел шлагбаума. Получает mode=usual (Машина въезжает) или
        mode=esc (машина выезжает). Суть в чем, если mode=usual, значит машина въезжает, можно смело закрывать открытый
        ей шлагбаум, по окончанию таймера, например, если на весах пусто.
        Но вот если mode=esc, значит машина выезжает, закрыть шлагбаум тогда можно только если wait_for_scale_idle
        вернет истину (т.е. фотоэлементы деблокированы а весы показывают меньше N (100кг, например))"""
        if mode == 'usual':
            self.close_gate(gate)
        else:
            self.wait_for_scale_idle(gate)

    def wait_for_scale_idle(self, gate):
        # Ждет пока весы освободятся, затем опускает стрелу
        while True:
            if self.check_scale_idle():
                self.close_gate(gate)
                break
            # Если все еще не освободились, подождать 2 секунды и повторить
            sleep(2)

    def check_course(self, course='any'):
        """ Возвращает TRUE, если фотоэлементы были пересечены с ожидаемого направления """
        self.show_notification('course is', course)
        # exit_photo_num (4), entry_photo_num (3), photo_unlock_state (30), photo_lock_state (31)
        occup = True
        if course == 'OUT':
            cur_point = s.exit_ph_num  # 4
            rev_point = s.entry_ph_num  # 3
        else:
            cur_point = s.entry_ph_num  # 3
            rev_point = s.exit_ph_num  # 4
        point = self.contr_stream[-1][4]
        self.show_notification('\n\tПоток слежения за точками доступа -', self.contr_stream)
        for k, v in self.ph_els.items():
            if course == 'any':
                if (point == s.exit_ph_num and k == s.exit_ph_num and v == s.ph_unlock_state
                        or point == s.entry_ph_num and k == s.entry_ph_num and v == s.ph_unlock_state):
                    return True
            elif course == 'OUT' or course == 'IN':
                if not self.streamParsePh(cur_point, occup, k, v, s.exit_ph_num, s.entry_ph_num, s.ph_unlock_state,
                                          s.ph_lock_state):
                    return True

    def streamParsePh(self, tracingPh, occup, k, v, *contr_els):
        # Новый способ слежения за фотоэлементами, который заключается
        # в слежке за всем потоком, а не только за последним пересечением
        s.exit_ph_num, s.entry_ph_num, s.ph_unlock_state, s.ph_lock_state = contr_els
        for rec in self.contr_stream:
            if rec[4] == tracingPh == k and v == s.ph_unlock_state:
                occup = False
            if rec[4] == tracingPh == k and v == s.ph_lock_state:
                occup = True
        return occup

    def take_weight(self):
        '''Взять последний вес из потока'''
        count = -1
        while count > -6:
            last_weight = self.weightlist[count]
            if last_weight is not None and type(last_weight) == str:
                weight = last_weight
                return weight
            else:
                count -= 1

    def points_tracing(self, data):
        """ Парсит сообщение об изменении состояния точек доступа от контроллера Скуд"""
        self.show_notification('\nПолучено состояние точек доступа: ', data)
        point, status = get_point_status(data)
        if point == s.entry_ph_num or point == s.exit_ph_num:
            self.cut_list(self.contr_stream, -15)
            self.contr_stream.append(data)
            self.fix_ph_el_status(point, status)
            self.show_notification('Обновление contr_stream:', self.contr_stream)
        else:
            self.show_notification('Ошибка!  Данные не подходят по структуре!')

    def fix_ph_el_status(self, point, status):
        # Получает сплитованные по пробелу данные от скуд контроллера и фиксирует положение о фотоэлементах
        self.ph_els[point] = status

    def get_weight(self, carnum, course='deff', mode='usual', recId='none'):
        """ Начать взвешивание и вернуть вес"""
        id_type = self.define_idtype('car_number', carnum)
        if self.polomka:
            weight = self.polomka_protocol(course, id_type)
        elif self.dlinnomer:
            weight = self.dlinnomer_protocol(course, id_type)
        else:
            weight = self.photo_scaling(course, id_type)
        # Сфотографировать весовую платформу
        self.makePic(carnum, mode, course, recId)
        if weight == '2' or weight == '1':
            self.send_error('Нет связи с весовым терминалом.')
            weight = self.operate_scale_error(weight)
        return weight

    def operate_scale_error(self, weight):
        # Если весы возвращают 1 или 2 (ошибка)
        while weight != 1 and weight != 2:
            # Впасть в цикл и пытаться переподключиться
            self.make_cps_connection()
            sleep(3)
            weight = self.add_weight()
        return weight

    def add_weight(self, mode='usual'):
        new_weight = self.wlistener.wlisten_tcp()
        self.show_notification('Catched weight is: ', new_weight)  # получает показания
        if mode == 'int':
            try:
                new_weight = int(new_weight)
            except:
                new_weight = 3
        self.weightlist = self.cut_list(self.weightlist)
        self.weightlist.append(new_weight)
        return new_weight

    def cut_list(self, listname, lastcount=-10):
        return listname[lastcount:]

    def get_ident1(self, carnum):
        ident1 = "car_number='{}'".format(carnum)
        return ident1

    def get_carnum_by_rfid(self, rfid_num):
        """ Вернуть гос.номер из таблицы по номеру RFID"""
        command = "SELECT car_number from {} WHERE rfid='{}' and active=True".format(s.auto, rfid_num)
        carnum = self.sqlshell.try_execute_get(command)
        self.show_notification('\tНомер авто получено:', carnum)
        return carnum[0][0]

    def close_open_records(self, carnum, info):
        # Закрыть все записи с этим номером с отметкой алерта
        self.alerts = s.alerts_description['no_exit']['description']
        command = "UPDATE {} set inside='no', cargo=0, tara=0, time_out='{}' " \
                  "where car_number='{}' and inside='yes'".format(s.book, info['timenow'], carnum)
        rec_id = self.sqlshell.try_execute(command)['info'][0][0]
        # self.protocol_ending(carnum, info['timenow'], course=info['course'], recId=rec_id)
        self.add_alerts(rec_id)
        self.updAddInfo(status='Протокол завершен', notes='Запись обновлена')

    def escaping(self, carnum, mode, contragent='none', trashcat='none',
                 trashtype='none', comm='none', operator='none'):
        """Функция инициации протокола выезда для авто"""
        self.show_notification('\nМашина', carnum, 'выезжает с полигона')
        self.open_gate(name='exit')  # Открыть шлагбаум
        weight = self.get_weight(carnum=carnum, course='OUT', mode=mode)  # Произвести взвешивание
        if self.if_car_not_passed(weight):  # Проверить, проехала ли машина
            self.close_gate_no_pass(gate_name='exit', course='OUT')  # Если нет, закрыть шлагбаум.
            return  # Прекратить выполнение функции
        # ident1 = self.get_ident1(carnum)
        timenow = self.get_timenow()
        if mode == 'correct':
            self.escCorrectProtocol(carnum, weight, timenow, comm)
        elif mode == 'incorrect':
            self.escIncorrectProtocol(carnum, weight, timenow)

    @try_except_decorator('Фотографирование грузовой платформы')
    def makePic(self, carnum, mode, course, recId='none'):
        if recId == 'none':
            recId = sup_funcs.get_rec_id(self.sqlshell, carnum)
        self.currentProtocolId = recId  # Доступ для других функций
        self.cam.make_pic(self.currentProtocolId)
        self.show_notification('\tФото сделано.')

    def escCorrectProtocol(self, carnum, weight, time, comm, mode='usual'):
        """Обычный (корректный) протокол выезда для авто"""
        # Получить брутто и ID заезда
        command = "SELECT brutto, id from {} WHERE inside='yes' and car_number='{}'".format(s.book, carnum)
        data = self.sqlshell.try_execute_get(command)
        brutto, recid = data[0]
        cargo = self.get_cargo(weight, brutto)  # Вычислить вес нетто
        self.alerts = self.sqlshell.check_car(cargo, self.alerts)
        if len(comm) > 0:  # Если есть новый комментарий, добавить
            comm = 'Выезд: {} '.format(comm)
        msg = "tara='{}', cargo='{}', time_out='{}',"
        msg += "inside='no', notes = notes || '{}'"

        if self.tara_is_more(brutto, weight):  # Если тара больше брутто
            msg += ", brutto='{}'"
            values = msg.format(brutto, abs(cargo), time, comm, int(weight))
        else:
            values = msg.format(int(weight), cargo, time, comm)

        command = "UPDATE {} set {} where inside='yes' and car_number='{}'".format(s.book, values, carnum)
        rec_id = self.sqlshell.try_execute(command)
        self.updAddInfo(notes='Запись обновлена')
        if mode != 'NEG' and mode != 'tails':
            self.show_notification('it is not NEG or tails mod! Mode is', mode)
            self.try_sleep_before_exit()
            self.open_gate(name='entry')
            self.protocol_ending(carnum, time, course='IN', recId=recid)

    def send_act(self):
        """ Оотправить акты на SignAll"""
        self.show_notification('\nОтправка актов на WServer')
        for wclient in self.all_wclients:
            try:
                sig_funcs.send_json_reports(self.sqlshell, wclient, self.poligon_id,
                                            table_to_file_dict=s.json_table_to_file.items())
                self.show_notification('\tАкты успешно отправлены')
                self.wserver_connected = True
            except:
                self.operate_exception('Не удалось отправить акты')
                health_monitor.change_status('Связь с WServer', False, format_exc())
                self.wserver_connected = False

    @try_except_decorator('time.sleep перед открытием въездного шлагбаума')
    def try_sleep_before_exit(self):
        """ Ожидает перед тем, как открыть въездной шлагбаум выезжающей машине. Использует конфиг пользователя"""
        sleep(self.sleep_time_after_ex_weight)

    def tara_is_more(self, brutto, tara):
        # Возвращает True, если тара больше брутто
        weight = int(tara) - int(brutto)
        if weight > 0:
            return True

    def escIncorrectProtocol(self, carnum, weight, time):
        """ Некорректный протокол выезда (нет взвешивания брутто) """
        values = "('{}', '{}', '{}', 'no', {}, {}, {}, {})".format(carnum, time, time, int(weight), 0, 0, 1)
        command = "INSERT INTO {} (car_number, time_in, time_out, inside, tara, brutto, cargo, operator) " \
                  "values {}".format(s.book, values)
        rec_id = self.sqlshell.try_execute(command)
        self.updAddInfo(notes='Запись обновлена')
        self.open_gate(name='entry')
        self.protocol_ending(carnum, time, course='IN', recId=rec_id)

    def get_cargo(self, weight, brutto):
        '''Получает cargo (cargo), как разницу между brutto и текущим весом'''
        cargo = int(brutto) - int(weight)
        return cargo

    def note_esc(self, course, mode):
        ''' Функция для фиксации выезда авто с cargoовой платформы '''
        self.show_notification('note_esc. course', course, 'mode', mode)
        try:
            self.check_ph_release(course, mode)
        except PhNotBreach:
            self.logger.error('Выход не зафиксирован фотоэлементом')

    def dlinnomer_protocol(self, course, id_type):
        """ Сценарий для спец.протокола длинномер"""
        # Поймать вес 1
        weight = self.catching_weight(course, id_type, only_breach=True)
        # Октыть вторые ворота
        second_gate = s.spec_orup_protocols[course]['second_gate']
        self.open_gate(name=second_gate)
        reverse_course = s.spec_orup_protocols[course]['reverse']
        weight_add = self.photo_scaling(reverse_course, id_type, only_breach=True)
        weight = str(int(weight) + int(weight_add))
        self.show_notification('\n\n\nСуммируем веса {} + {}'.format(str(weight), str(weight_add)))
        return weight

    def polomka_protocol(self, course, id_type):
        sleep(1)
        second_gate = s.spec_orup_protocols[course]['second_gate']
        self.open_gate(name=second_gate)
        weight = self.photo_scaling(course, id_type)
        return weight

    def entering(self, carnum, timenow, trashtype='none', trashcat='none',
                 contragent='none', comm='none', operator='none'):
        """ Сценарий заезда по протоколу Usual (rfid) """
        self.show_notification('\nИнициирован протокол заезда')
        self.open_gate(name='entry')
        self.show_notification('\tПолучаю вес..')
        weight = self.get_weight(carnum=carnum, course='IN')
        if self.if_car_not_passed(weight):
            self.close_gate_no_pass(gate_name='entry', course='IN')
            return
        self.show_notification('\t\tВес получен', weight)
        # Если машины нет в таблице auto - зарегистрировать ее
        template = '(car_number, brutto, time_in, inside, carrier, trash_type, trash_cat, notes, operator)'
        if len(comm) > 0:
            comm = 'Въезд: {} '.format(comm)
        rec_id = self.sqlshell.create_str('records', template,
                                          "('{}',{},'{}','yes',{},{},{},'{}',{})".format(carnum, weight, timenow,
                                                                                            contragent,
                                                                                            trashtype, trashcat, comm,
                                                                                            operator))
        self.updAddInfo(notes='Запись обновлена')
        self.open_gate(name='exit')
        self.protocol_ending(carnum, timenow, course='OUT', recId=rec_id)

    def if_car_not_passed(self, weight, min_weight=s.min_weight_car_on_scale):
        """ Возвращает True, если машина на проехала на весы (фотоэлменты не пересеклись + весы показывают малый вес)"""
        if weight == None: weight = 0
        if self.phNotBreach == True and not self.check_car_on_scale(weight, min_weight):
            self.show_notification('CAR DID NOT PASS')
            self.updAddInfo(status='Время истекло!')
            return True

    @try_except_decorator('Обновление last_events')
    def add_alerts(self, rec_id):
        '''Попытка добавить алерты в disputs'''
        self.sqlshell.add_alerts(self.alerts, rec_id)

    def getKeyCommand(self, tablename, target, ident):
        command = '(select {} from {} where {})'.format(target, tablename, ident)
        return command

    def close_gate_no_pass(self, gate_name, course):
        """ Закрыть шлагбаум, когда машина не проехала """
        self.close_gate(gate_name)
        if self.polomka:
            # Если это протокол "Поломка" - тогда закрыть и вторые ворота
            sleep(1)
            self.close_gate(s.spec_orup_protocols[course]['second_gate'])

    def get_anim_info(self, course, id_type, status):
        # Возвращает данные об анимации, исходя из направления машины, типа и статуса протокола
        print(locals())
        anim_info = {}
        current_info = s.protocols_anim_info[id_type][course]
        anim_info['face'] = current_info['face']
        anim_info['pos'] = current_info[status]
        return anim_info

    def send_anim_info(self, course, id_type, status, carnum=None):
        # Отправляет информацию о положении авто для отрисовки анимации
        anim_info = self.get_anim_info(course, id_type, status)
        if carnum:
            anim_info['carnum'] = carnum
        command = self.formCommand('anim_info', anim_info)
        #self.wlistener.broadcastMsgSend(command)
        threading.Thread(target=self.wlistener.broadcastMsgSend, args=(command,)).start()

    def neg_close_record(self, carnum, timenow, comm, course):
        # Закрыть заезд по протоколу NEG (no exit group)
        gate_name = s.spec_orup_protocols[course]['first_gate']
        self.open_gate(name=gate_name)
        weight = self.get_weight(carnum=carnum, course=course, mode='NEG_OUT')
        if self.if_car_not_passed(weight):
            self.close_gate_no_pass(gate_name=gate_name, course=course)
            return
        self.show_notification('\n\tCar was on territory.')
        ident1 = self.get_ident1(carnum)
        self.escCorrectProtocol(carnum, weight, timenow, comm, mode='NEG')
        sleep(2)
        self.open_gate(name=gate_name)
        self.protocol_ending(carnum, timenow, course=course, mode='tails')

    def neg_init_record(self, carnum, timenow, trashcat, trashtype, contragent, comm, operator, course):
        # Начать заезд по протоколу NEG (no exit group)
        self.open_gate(name=s.spec_orup_protocols[course]['first_gate'])
        weight = self.get_weight(carnum=carnum, course=course, mode='NEG_IN')
        if self.if_car_not_passed(weight):
            self.close_gate_no_pass(gate_name=s.spec_orup_protocols[course]['first_gate'], course=course)
            return
        self.show_notification('\n\tCreating record for new car.')
        if len(comm) > 0:
            comm = 'Въезд: {} '.format(comm)
        rec_id = self.sqlshell.create_str(s.book,
                                          '(car_number, time_in, inside, trash_cat, trash_type, carrier, notes, '
                                          'operator, brutto)',
                                          "('{}','{}', 'yes', ({}),({}),({}),'{}', ({}), '{}')".format(
                                              carnum, timenow, trashcat, trashtype, contragent, comm, operator, weight))
        self.updAddInfo(notes='Запись обновлена')
        sleep(2)
        self.open_gate(name=s.spec_orup_protocols[course]['first_gate'])
        self.protocol_ending(carnum, timenow, course=course, recId=rec_id, mode='tails')

    def across_group(self, carnum, timenow, course, *args, **kwargs):
        # Начать заезд с открытием обоих шлагбаумов и без взвешивания
        self.open_gate(name=s.spec_orup_protocols[course]['first_gate'])
        self.check_ph_release(course, only_breach=False)
        self.open_gate(name=s.spec_orup_protocols[course]['second_gate'])
        self.protocol_ending(carnum, timenow, course)

    def tails_group_close_record(self, carnum, timenow, comm, course):
        # Закрыть открытый заезд
        self.show_notification('\n\t CAR WAS IN THE AREA')
        self.open_gate(name=s.spec_orup_protocols[course]['first_gate'])
        self.show_notification('\tПолучаю вес..')
        weight = self.get_weight(carnum=carnum, mode='tails', course=course)
        if self.if_car_not_passed(weight):
            self.close_gate_no_pass(gate_name=s.spec_orup_protocols[course]['first_gate'], course=course)
            return
        self.show_notification('\tВес получен', weight)
        ident1 = self.get_ident1(carnum)
        self.escCorrectProtocol(carnum, weight, timenow, comm, mode='tails')
        self.open_gate(name=s.spec_orup_protocols[course]['second_gate'])
        self.protocol_ending(carnum, timenow, course=s.spec_orup_protocols[course]['reverse'])

    def tails_group_init_record(self, carnum, timenow, trashcat, trashtype, contragent, comm, operator, course):
        # Инициировать новый заезд
        self.show_notification('\n\t CREATING STR FOR NEW CAR')
        self.open_gate(name=s.spec_orup_protocols[course]['first_gate'])
        weight = self.get_weight(carnum=carnum, mode='tails', course=course)
        if self.if_car_not_passed(weight):
            self.close_gate_no_pass(gate_name=s.spec_orup_protocols[course]['first_gate'], course=course)
            return
        if len(comm) > 0:
            comm = 'Въезд: {} '.format(comm)
        self.show_notification('\tВес получен', weight)
        rec_id = self.sqlshell.create_str(s.book,
                                          '(car_number, time_in, inside, trash_cat, trash_type, Carrier, notes, '
                                          'operator, brutto)',
                                          "('{}','{}', 'yes', {},{},{},'{}', ({}), '{}')".format(
                                              carnum, timenow, trashcat, trashtype, contragent, comm, operator, weight))
        self.updAddInfo(notes='Запись обновлена')
        self.open_gate(name=s.spec_orup_protocols[course]['second_gate'])
        self.protocol_ending(carnum, timenow, course=s.spec_orup_protocols[course]['reverse'], recId=rec_id)

    def protocol_ending(self, carnum, timenow, course, recId='none', mode='random'):
        """ Общие операции, завершающие протокол выезда и въезда"""
        self.show_notification('\n\tЗавершающие операции')
        self.phNotBreach = False
        self.dlinnomer = 0
        self.polomka = 0
        self.note_esc(course, mode='esc')
        id_type = self.define_idtype('car_number', carnum)
        if recId == 'none' and type(self.currentProtocolId) == str:
            recId = self.currentProtocolId.strip('IN')
            recId = recId.strip('OUT')
        if not s.GENERAL_DEBUG:
            self.alerts = self.sqlshell.check_car_choose_mode(self.alerts, self.choose_mode, carnum,
                                                              s.spec_orup_protocols[course]['reverse'])
        if s.AR_DUO_MOD:
            self.send_acts_duo_mode(recId)
        self.add_alerts(recId)
        #threading.Thread(target=self.send_act, args=()).start()
        self.choose_mode = 'auto'
        self.show_notification('Последний заезд успешно сохранен. Теперь lastvisit-', self.lastVisit)
        sleep(1)
        anim_info = self.get_anim_info(s.spec_orup_protocols[course]['reverse'], id_type, 'end_pos')
        self.updAddInfo(status='Протокол завершен', face=anim_info['face'], pos=anim_info['pos'])
        self.show_notification('\n##############################################')
        self.show_notification('*** Протокол завершен ***')
        self.show_notification('\tStatus -', self.wlistener.status)
        self.show_notification('#############################################\n')

    def send_acts_duo_mode(self, record_id):
        duo_functions.records_owning_save(self.sqlshell, s.records_owning_table, s.pol_owners_table,
                                          self.polygon_name, record_id)
        try:
            duo_functions.send_act_by_polygon(self.all_wclients, self.sqlshell, s.connection_status_table,
                                             s.pol_owners_table)
        except: print(format_exc())

    def define_gate_point_hname(self, name):
        gate_num = s.gates_info_dict[name]['point']
        hname = s.gates_info_dict[name]['hname']
        return gate_num, hname

    def open_gate(self, name):
        """ Открыть шлагбаум """
        self.show_notification('Открываем шлагбаум ', name)
        gate_num, hname = self.define_gate_point_hname(name)
        data = '{} шлагбаум открывается.'.format(hname)
        self.send_cm_info('sysInfo', 'data', data)
        send_open_gate_command(self.sock, gate_num)
        self.show_notification('Шлагбаум открыт')

    def close_gate(self, name):
        """ Закрыть шлагбаум """
        self.show_notification('Закрываем шлагбаум ', name)
        gate_num, hname = self.define_gate_point_hname(name)
        data = '{} шлагбаум закрывается.'.format(hname)
        self.send_cm_info('sysInfo', 'data', data)
        send_close_gate_command(self.sock, gate_num)
        threading.Thread(target=self.gate_close_control_thread,
                         args=(name, s.gates_info_dict[name]['close_time'])).start()
        self.show_notification('Шлагбаум закрыт.')

    def gate_close_control_thread(self, name, time_to_close):
        """ Механизм контроллирования за закрытием шлагбаума """
        timer = time_to_close
        count = 0
        # Извлекаем старое количество данных с контроллера Skud
        os = len(self.contr_stream)
        while timer != 0:
            self.show_notification('\n\n\n\nCLOSE MECH STARTED for', name, debug=True)
            # Если произошлое событие на контроллере СКУД и оно связано с фотоэлементами)
            if (self.check_if_new_contr_mess(os) and self.contr_stream[-1][4] == s.entry_ph_num
                    or self.check_if_new_contr_mess(os) and self.contr_stream[-1][4] == s.exit_ph_num):
                if self.check_course(s.gates_info_dict[name]['course']):
                    # Если это с ожидаемой стороны, все норм
                    count += 1
                    timer = time_to_close
                    self.show_notification('\n\n\n\n\nc1', count, timer, name, debug=True)
                else:
                    # Если нет - игнор
                    timer -= 1
                    count = 0
                    self.show_notification('\n\n\n\n\n\nc2', count, timer, name, debug=True)
            # Если же событий не произошло - игнор
            else:
                count = 0
                timer -= 1
                self.show_notification('c3', count, timer, name, debug=True)
            sleep(1)
            if count > 1:
                self.show_notification('\n\nПерезакрытие!')
                self.open_gate(name)
                sleep(4)
                self.close_gate(name)
                break

    def car_detect_operate(self, rfid, course):
        """ Если появилась команда carDetected (Система увидела машину) """
        print(locals())
        if rfid != 'nopass' and self.sqlshell.check_access(rfid):
            idtype = self.define_idtype('rfid', rfid)
            self.operateCM(rfid, course, idtype)

    def define_idtype(self, mode, value):
        ident = "{}='{}'".format(mode, value)
        try:
            command = "SELECT id_type from {} where {}".format(s.auto, ident)
            idtype = self.sqlshell.try_execute_get(command)[0][0]
        except IndexError:
            idtype = 'tails'
        return idtype

    def operateCM(self, rfid, course, idtype):
        """ Если система зафиксировала машину с меткой, зарегистрированной в БД"""
        self.show_notification('\noperateCM: status -', self.wlistener.status)
        # if self.wlistener.status == 'Готов':
        #    self.wlistener.status = 'waitingCM'
        canPass = True
        carnum = self.get_carnum_by_rfid(rfid)
        self.show_notification('\tПытаемся достать время последнего заезда авто')
        try:
            lastVisitDate = self.lastVisit[carnum]
            self.show_notification('\t\tУспешно.Последний заезд:', lastVisitDate)
            now = datetime.now()
            passed = now - lastVisitDate
            passed = passed.total_seconds()
            self.show_notification('\t\tПрошло времени:', passed)
            if passed > s.carDetectTimeOut and self.wlistener.status != 'Занят':
                self.show_notification('\t\tМожно отправить CarDetect', self.wlistener.status)
                canPass = True
            else:
                self.show_notification('\t\tНельзя отправить CarDetect', self.wlistener.status)
                canPass = False
                # self.update_status('Готов')
        except:
            self.show_notification('\tНе удалось достать время последнего заезда авто')
            # print(format_exc())
        if canPass:
            have_brutto = self.check_car_have_brutto(carnum)
            if s.ASU_ROUTES:
                must_be_tko = check_if_car_tko(self.sqlshell, carnum, s.asu_routes_table, s.auto)
            else:
                must_be_tko = False
            ident = "auto.car_number='{}'".format(carnum)
            command = "select carrier, trash_type, trash_cat "
            command += "from last_events inner join auto on "
            command += "(last_events.car_id=auto.id) "
            command += "where {}".format(ident)
            last_data = self.sqlshell.try_execute_get(command)
            self.show_notification('Получена last_data', last_data)
            try:
                lastContragent = last_data[0][0]
                lastTrashType = last_data[0][1]
                if s.ASU_ROUTES and must_be_tko:
                    try:
                        get_tko_id(self.sqlshell, s.trash_cats_table)
                    except:
                        lastTrashCat = last_data[0][2]
                else:
                    lastTrashCat = last_data[0][2]
            except:
                lastContragent = 0
                lastTrashType = 0
                lastTrashCat = 0
            msg = {'carDetected': {'carnum': carnum, 'course': course,
                                   'lastContragent': lastContragent, 'weight': 'null',
                                   'lastTrashType': lastTrashType, 'lastTrashCat': lastTrashCat, 'id_type': idtype,
                                   'have_brutto': have_brutto, 'must_be_tko': must_be_tko}}
            self.show_notification('Сообщение для СМ сформировано:', msg)
            #self.wlistener.broadcastMsgSend(msg)
            threading.Thread(target=self.wlistener.broadcastMsgSend, args=(msg,)).start()

    def check_car_have_brutto(self, carnum):
        # Возвращает True, если машина уже взвесила брутто
        if self.sqlshell.check_car_inside(carnum, s.book):
            return True

    def update_status(self, status):
        '''Функция обновления статуса готовности AR'''
        # self.status = status
        self.wlistener.status = status

    def updAddInfo(self, **kwargs):
        '''Функция добавления информации в словарь обмена'''
        for k, v in locals()['kwargs'].items():
            self.addInfo[k] = v
        status = self.formStatusCommand()
        threading.Thread(target=self.wlistener.broadcastMsgSend, args=(status,)).start()

    def formCommand(self, command, info):
        command = {command: info}
        return command

    def formStatusCommand(self):
        command = self.formCommand('updateStatus', self.addInfo)
        return command

    def operate_skud_stream(self):
        '''Получение rfid num'''
        self.show_notification('\tПолучаем данные от Sigur. Status', self.wlistener.status)
        data = self.get_skud_data(self.sock)
        datalist = data.split('\r\n')
        for data in datalist:
            data_split = data.split(' ')
            if len(data_split) == 9 and data_split[7] == 'W42':
                course = s.courses[data_split[6]]
                #if s.MIRRORED:
                #    if course == 'OUT':
                #       course = 'IN'
                #    else:
                #       course = 'OUT'
                rfid = data_split[-1].replace('\r\n', '')
                self.show_notification('\t\tПолучены rfid, course:', rfid, course)
                self.car_detect_operate(rfid, course)
            if len(data_split) == 8:
                self.points_tracing(data_split)
            else:
                self.show_notification('\t\tUNDEFINED DATA:', data)

    def get_skud_data(self, socket):
        data = socket.recv(1024)
        data = data.decode()
        self.show_notification('\t\tПолучены данные от SIGUR:', data)
        return data

    @try_except_decorator('Установка конфиг-файла оператора')
    def installUserCfg(self, username='none', user_id='none'):
        # Устанавливает конфиг пользователя. Сначала достает кфг файл из таблицы,
        # затем задает их атрибутам
        cfg = self.getUserCfg(user_id, username)
        self.setUserCfg(cfg)

    def getUserCfg(self, user_id, username):
        '''Получает имя пользователя или его id и возвращает конфиг этого юзера'''
        command = "select sleep_time_after_ex_weight, rfid_buffer_size "
        command += "from user_configs inner join users on "
        command += "(users.config=user_configs.id) "
        if user_id != 'none':
            # Если передали id
            command += "where users.id='{}'".format(user_id)
        elif username != 'none':
            # Если передали имя
            command += "where users.username='{}'".format(username)
        response = self.sqlshell.try_execute_get(command)
        response = response
        self.show_notification('RESPONSE FROM GET USR CFG', response)
        return response

    def setUserCfg(self, response):
        # Устанавливает cfg пользователя
        self.sleep_time_after_ex_weight = response[0][0]
        self.rfid_buffer_size = response[0][1]

    def work(self):
        subscribe_ce(self.sock)
        while True:
            try:
                self.operate_skud_stream()
            except KeyboardInterrupt:
                os._exit(0)

    def send_error(self, error_text):
        error_text = {'error_text': error_text}
        self.found_errors.append(error_text)
        self.cut_list(self.found_errors, -15)
        command = self.formCommand('faultDetected', error_text)
        #self.wlistener.broadcastMsgSend(command)
        threading.Thread(target=self.wlistener.broadcastMsgSend, args=(command,)).start()

    def send_cm_info(self, title, subtitle, info):
        data = {subtitle: info}
        command = self.formCommand(title, data)
        threading.Thread(target=self.wlistener.broadcastMsgSend, args=(command,)).start()

    def opl_create_file(self, carnum):
        datetime = self.get_timenow()
        if type(datetime) != str:
            date = datetime.strftime(' %Y.%m.%d %H:%M:%S')
        else:
            date = datetime
        file_name = carnum + ' ' + date
        self.opl_file = os.path.join(s.opl_dirname, file_name)
        with open(self.opl_file, 'w') as fobj:
            fobj.write('### CREATED NEW LOG FOR {} IN {} ###\n'.format(carnum, datetime))

    def opl_make_record(self, record):
        log_file = self.get_opl_filename()
        with open(log_file, 'a') as fobj:
            fobj.write(record)
            fobj.write('\n')

    def get_opl_filename(self):
        try:
            log_file = self.opl_file
        except:
            log_file = s.opl_dirname + os.sep + 'undefined_log'
        return log_file

    def join_tuple_string(self, msg):
        return ' '.join(map(str, msg))

    def show_notification(self, *args, debug=False):
        args = self.join_tuple_string(args)
        self.opl_make_record(args)
        if debug and self.debug:
            print(datetime.now(), args)
        elif not debug:
            print(datetime.now(), args)
