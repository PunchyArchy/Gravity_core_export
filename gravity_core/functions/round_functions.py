"""
Содержит функции применяемые в ходе раунда (взвешивания)
(ЗАБРОШЕНО ДО РЕАЛИЗАЦИИ КЛАССА RECORDER!!!)
"""


import datetime
from gravity_core import wsettings as s
from gravity_core.functions import srl_functions


def start_car_weighing_round(sqlshell, car_number, comm, course, car_choose_mode='manual', dlinnomer=0, polomka=0,
                             operator=1, carrier=1, trash_cat=1, trash_type=1, old_car_number=None, polygon_object=None):
    """ Начать раунд """
    car_protocol = define_idtype(sqlshell, 'car_number', car_number)          # Выяснить протокол заезда этой машины
    have_brutto = check_car_inside(sqlshell, car_number)                 # Выяснить есть ли у данного авто брутто
    timenow = datetime.now()                                        # Выяснить текущее время
    pre_any_protocol_operations(info)                               # Пред-стартовые операции
    if have_brutto:
        # Если машина уже взвесила брутто
        operate_orup_exit_commands(info)
    else:
        # Если же машина первый раз въезжает на территорию
        pre_open_protocol_operations(info)
        operate_orup_enter_commands(info)


def define_idtype(sqlshell, mode, value, auto_table=s.auto, *args, **kwargs):
    ident = "{}='{}'".format(mode, value)
    try:
        command = "SELECT id_type from {} where {}".format(auto_table, ident)
        idtype = sqlshell.try_execute_get(command)[0][0]
    except IndexError:
        idtype = 'tails'
    return idtype


def check_car_inside(sqlshell, carnum, records_table=s.records_table, *args, **kwargs):
    """ Проверяет находится ли машина на территории предприятия """
    command = "SELECT EXISTS (SELECT * FROM {} where car_number='{}' and inside='yes' LIMIT 1)".format(records_table,carnum)
    response = sqlshell.try_execute_get(command)[0][0]
    return response


def pre_any_protocol_operations(car_number, car_choose_mode, slr_dirname, *args, **kwargs):
    # Операции, которые необходимы быть выполнены перед началом любого протокола
    srl_functions.srl_create_file(car_number, slr_dirname)
    define_if_polomka_or_dlinnomer(info)
    lastVisit[info['carnum']] = info['timenow']
    anim_info = get_anim_info(info['course'], info['car_protocol'], 'start_pos')
    # ФРИЗ ЗДЕСЬ ERROR
    updAddInfo(status='Начало взвешивания', carnum=info['carnum'], face=anim_info['face'],
                    pos=anim_info['pos'])
    alerts = ''