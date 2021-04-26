from pathlib import Path
import os

# Debug mods
GENERAL_DEBUG = True            # Общий дебаг (вывод сообщений в общий поток вывода)
SQLSHELL_DEBUG = False          # Режим дебага Sqlshell
WS_DEBUG = False                # Режим дебага WeightSplitter
WAPI_DEBUG = False              # Режим дебага WAPI
PROTOCOLS_DEBUG = False         # Режим дебага протоколов (взвешивание без машины)

# SETTINGS
IMPORT_FTP = False              # Импорт клиентов с FTP
MIRRORED = True 	        	# False = Въезд - справа, выезд - слева

# MODS
TEST_MODE = True
AR_DUO_MOD = True

# NEW_SETTINGS
PROJECT_NAME = 'gravity_core'
BASE_DIR = Path(__file__).resolve().parent.parent
INTERNAL_DIR = os.path.join(BASE_DIR, PROJECT_NAME)
CUR_DIR = os.path.dirname(os.path.abspath(__file__))

# Folders
rootdir = os.getcwd()
tmp_dir = os.path.join(INTERNAL_DIR, 'tmp')
reports_dir = os.path.join(INTERNAL_DIR, 'reports')
logs_dir = os.path.join(INTERNAL_DIR, 'logs')
sys_logs = os.path.join(logs_dir, 'sys_logs')
camera_folder = os.path.join(INTERNAL_DIR, 'camera_folder')

#project_dir = os.abspath('.')

# Отправка логов 18000-7200-3605
logs_send_rate = 600
logs_check_rate_1c = 1800
logs_check_rate = 1800

#Отправка логов по конкретному времени
reports_time = ["08:15", "10:00", "11:00", "11:50", "13:00", "15:00", "17:00", "20:00", "20:40"]

#reports_time = ["13:27"]
#1c данные
timeStamp = 'tbo_oN.txt'                           # название файла от 1с
#startTime = os.'startTime' # назначение
reports_1c_dir = os.sep.join((reports_dir, '1c_reports'))
reports_json_dir = os.sep.join((reports_dir, 'json_reports'))

#rfid_logs_dir_1с = os.sep.join((reports_dir, 'new_rfid_log'))
#rfid_logs_1c_xml = os.sep.join((reports_1c_dir, 'new_rfid.xml'))
rfid_logs_1c_xml_ext = os.sep.join((reports_1c_dir, 'new_rfid_ext.xml'))
#rfid_logs_1c_xml_1pol = os.sep.join((reports_1c_dir, 'new_rfid_1pol.xml'))
#rfid_logs_1c_xml_ext_1pol = os.sep.join((reports_1c_dir, 'new_rfid_ext_1pol.xml'))

# Json reports
reports_json = os.sep.join((reports_json_dir, 'json_reports'))
cars_json = os.sep.join((reports_json_dir, 'json_cars'))
clients_json = os.sep.join((reports_json_dir, 'json_clients'))
operators_json = os.sep.join((reports_json_dir, 'json_operators'))
cm_events_json = os.sep.join((reports_json_dir, 'cm_events_log'))

rfid_logs_ftp = '/ftp/new_rfid_log'

# CM events
cm_events_log_table = 'cm_events_log'
cm_events_table = 'cm_events_table'
cm_start_event = 'START'
cm_stop_event = 'STOP'
cm_login_event = 'LOGIN'

current_errors = {}

# One Protocol Log
opl_dirname = os.path.join(logs_dir, 'opl_logs')

json_table_to_file = {
    'clients': clients_json,
    'auto': cars_json,
    'users': operators_json,
    'records': reports_json,
    'cm_events_log': cm_events_json,
}


# CPS settings
scale_splitter_ip = '0.0.0.0'
my_ip = '0.0.0.0'
scale_splitter_port = 2297

scale_lis_time = 5
scale_est_time = 3
diff_value = 2000
twt = 0
twtesc = 0
after_wait_time = 0

#ДБ PostgreSQL
db_name = 'wdb'
db_user = 'watchman'
db_pass = 'hect0r1337'
db_location = '0.0.0.0'
clients_table = 'Clients'
last_events_table = 'last_events'
day_disputs_table = 'day_disputs'
disputs_table = 'disputs'
records_table = 'records'
auto = 'auto'
book = 'records'
pol_owners_table = 'pol_owners_table'
connection_status_table = 'duo_connection_status'
records_owning_table = 'duo_records_owning'

#ДБ signAll
#gdb_name = 'gdb'
#gdb_user = 'watchman'
#gdb_pass = 'hect0r1337'
#gdb_location = '192.168.100.118'
gdb_companies_table = 'companies'
gdb_records_table = 'records'
gdb_poligon_name = 'Мелеуз'
gdb_poligon_password = 'sun21'
gdb_poligons_table = 'poligons'

#Параметры для wcheker`a
ad_pc_this = 1.5
ad_pc_model = 2
ad_pc_all = 0.8
ad_ret_time = 7200
ad_in_time = 3600
ignore_deviations = True

# Время
ad_re_time = 7200
ad_pr_time = 3600
rfid_buffer_size = 3		# Размер буфера RFID

#Настройки контроллера СКУД
contr_ip = 'localhost'
contr_port = 3312
entry_gate_num = '2'
exit_gate_num = '1'
entry_ph_num = '3'
exit_ph_num = '4'

#if MIRRORED:
#    entry_ph_num = '4'
#    exit_ph_num = '3'
ph_lock_state = '31'
ph_unlock_state = '30'
courses = {'1': 'OUT',
           '2': 'IN'}

gates_info_dict = {'entry': {'point': entry_gate_num, 'hname': 'Внешний', 'course': 'IN', 'close_time': 6},
                   'exit': {'point': exit_gate_num, 'hname': 'Внутренний', 'course': 'OUT', 'close_time': 6},
                   'inning': {'point': entry_gate_num, 'hanme': 'Внутренний', 'course': 'IN', 'close_time': 6}}
#FTP settings
ftp_ip = '192.168.100.118'
ftp_login = 'pol1'
ftp_pw = 'hect0r1337'

newFtp_ip = '192.168.100.118'
newFtp_login = 'pol1'
newFtp_pw = 'hect0r1337'

# Выгрузка с 1С
clients_file = 'tbo_oN.txt'
clients_localfile = os.sep.join((tmp_dir, clients_file))
clients_file_ftp = os.sep.join(('/ftp', clients_file))

#Настройки TCP прослушивателя весов
scale_ip = '0.0.0.0'
scale_port = 2290

#Настройка сокета для передачи статуса  Watchman-CM
statusSocketIp = '0.0.0.0'
statusSocketPort = 2291
carDetectTimeOut = 60					# Игнорирует машину и не создает для нее новые CarDetect комманды в течение этого времени после последнего заезда

#Настройки камеры
cam_login = 'admin'
cam_pw = 'Assa+123'
cam_ip = '172.16.2.46'
pics_folder = os.path.join(camera_folder, 'pics')
count_file = os.path.join(camera_folder, 'cam_count.cfg')
fpath_file = os.path.join(camera_folder, 'fpath.cfg')

#Настройка реакции на фотоэлементы
ph_time = 7
ad_weight_rfid = 500
lib_time = 4
ph_release_timer = 60

#RFIDE RESUB
rfid_resub = 60

#Механизм ожидания выравнивания перед фотоэлементами
if PROTOCOLS_DEBUG:
    min_weight_car_on_scale = 0         # Минимальный вес на весах, что бы протокол мог быть продолжен
    min_weight_ph_checking = 0          # Минимальный вес для проверки о том, что после пересечения фотоэлементов машины на весах
    stable_win_weight = 0               # Минимальный вес, необходимый для начала ловли скачков веса после пересечения
else:
    min_weight_car_on_scale = 250        # Минимальный вес на весах, что бы протокол мог быть продолжен
    min_weight_ph_checking = 500         # Минимальный вес для проверки о том, что после пересечения фотоэлементов машины на весах
    stable_win_weight = 500              # Минимальный вес, необходимый для начала ловли скачков веса после пересечения

scale_idle_param = 50               # Минимальный вес, что бы решить, что весы свободны

max_wait = 60

diffRepEx = 2700

#Настройки сокета для получения комманд от Watchman-CM
cmUseInterfaceOn = True
cmUseInterfaceIp = '0.0.0.0'
cmUseInterfacePort = 2292
cm_sql_operator_port = 2293

#WServer settings
wserver_ip = '192.168.234.252'
wserver_port = 3001
wserver_reciever_port = 2295
wserver_reconnect_try_amount = 1    # количество попыток подключения после неудачи


# Взвешивание по стабилизации
stable_scaling_wait_time = 3        # Данные, полученные в течение этого кол-ва секунд, должны быть около равными
admitting_spikes = 50               # Допустимые скачки показателей для принятия веса

#ALERTS
alerts_description = {'fast_car': {'code': 'A7|', 'description': 'Машина слишком быстро вернулась ({})|', 'time': 900},
                      'cargo_null': {'code': 'W3|', 'description': 'Нетто около нуля|', 'null': 60},
                      'no_exit': {'code': 'A9|', 'description': 'Для данного авто не была взвешена тара|'},
                      'manual_pass': {'code': 'A0|', 'description': 'Ручной пропуск. Направление {}|'},
                      'no_rfid': {'code': 'A1|', 'description': 'Машина без метки|'},
                      'ph_el_locked': {'code': 'A1|', 'description': 'Фотоэлемент заблокирован|'}
                      }

# Протоколы NEG и Tails
spec_orup_protocols = {'IN': {'first_gate': 'entry', 'second_gate': 'exit', 'course_name': 'въезд', 'reverse': 'OUT'},
                       'OUT': {'first_gate': 'exit', 'second_gate': 'entry', 'course_name': 'выезд', 'reverse': 'IN'},
                       'inning': {'course_name': 'въезд'}}

if not MIRRORED:
#if True:
    protocols_anim_info = {'NEG':
                               {'IN': {'face': 'exit', 'start_pos': 'r', 'middle_pos': 'c', 'end_pos': 'r'},
                                 'OUT': {'face': 'enter', 'start_pos': 'l', 'middle_pos': 'c', 'end_pos': 'l'}},
                           'tails':
                               {'IN': {'face': 'exit', 'start_pos': 'r', 'middle_pos': 'c', 'end_pos': 'l'},
                                 'OUT': {'face': 'enter', 'start_pos': 'l', 'middle_pos': 'c', 'end_pos': 'r'}},
                           'rfid':
                               {'IN': {'face': 'exit', 'start_pos': 'r', 'middle_pos': 'c', 'end_pos': 'l'},
                                'OUT': {'face': 'enter', 'start_pos': 'l', 'middle_pos': 'c', 'end_pos': 'r'}}
                           }
else:
    protocols_anim_info = {'NEG':
                               {'IN': {'face': 'enter', 'start_pos': 'l', 'middle_pos': 'c', 'end_pos': 'l'},
                                 'OUT': {'face': 'exit', 'start_pos': 'r', 'middle_pos': 'c', 'end_pos': 'r'}},
                           'tails':
                               {'IN': {'face': 'enter', 'start_pos': 'l', 'middle_pos': 'c', 'end_pos': 'r'},
                                 'OUT': {'face': 'exit', 'start_pos': 'r', 'middle_pos': 'c', 'end_pos': 'l'}},
                           'rfid':
                               {'IN': {'face': 'enter', 'start_pos': 'l', 'middle_pos': 'c', 'end_pos': 'r'},
                                'OUT': {'face': 'exit', 'start_pos': 'r', 'middle_pos': 'c', 'end_pos': 'l'}}
                           }
