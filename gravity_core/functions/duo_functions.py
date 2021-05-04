""" Пакет функций для модификации DUO (несколько хозяев полигонов """
from witapi.main import WITClient
from gravity_core import health_monitor
from datetime import datetime
import threading
from traceback import format_exc
from time import sleep
from gravity_core.reports import signall_reports_funcs as sig_funcs
from gravity_core import wsettings as s


def get_all_polion_names(sqlshell, pol_owners_table):
    """ Извлечь все названия полигонов из pol_owners_table"""
    command = "SELECT name FROM {}".format(pol_owners_table)
    response = sqlshell.try_execute_get(command)
    poligon_names = [pol_info[0] for pol_info in response]
    return poligon_names


def get_all_poligon_connections(sqlshell, pol_owners_table, wserver_ip, wserver_port, wapi_debug=False):
    """ Возвращает словарь, содержащий словари, где ключ - poligon_name, а во вложенном
    словаре ключу wclient присваивается объект подключения (wclient)"""
    all_poligon_connections = {}
    poligon_names = get_all_polion_names(sqlshell, pol_owners_table)
    for poligon_name in poligon_names:
        gdb_poligon_name, gdb_poligon_password = fetch_poligon_authinfo(sqlshell, poligon_name)
        pol_con = create_wserver_connection(poligon_name, wserver_ip, wserver_port, gdb_poligon_name,
                                            gdb_poligon_password, wapi_debug)
        all_poligon_connections.update(pol_con)
    return all_poligon_connections


def fetch_poligon_authinfo(sqlshell, poligon_name):
    command = "SELECT login, password FROM duo_pol_owners where name='{}'".format(poligon_name)
    login, password = sqlshell.try_execute_get(command)[0]
    return login, password


def create_wserver_connection(connection_name, wserver_ip, wserver_port, gdb_poligon_name, gdb_poligon_password, wapi_debug=False):
    """ Создать подключение к WServer"""
    connection = {}
    wclient = WITClient(wserver_ip, wserver_port, gdb_poligon_name, gdb_poligon_password, debug=wapi_debug)
    # Попытаться подключиться
    connection[connection_name] = {}
    connection[connection_name]['wclient'] = wclient
    return connection


def fetch_wserver_connection_status(sqlshell, connection_status_table, pol_owners_table, poligon_name):
    """ Вернуть статус подключения полигона к WServer """
    command = "SELECT connected FROM {} WHERE poligon=(SELECT id FROM {} WHERE name='{}')".format(connection_status_table,
                                                                                             pol_owners_table,
                                                                                             poligon_name)
    print("Command is", command)
    response = sqlshell.try_execute_get(command)
    print("Response is", response)
    try:
        status = response[0][0]
    except IndexError:
        print(format_exc())
        status = False
    return status


def set_wserver_connected_status(sqlshell, connection_status_table, pol_owners_table, poligon_name, wserver_id):
    """ Установить статус подключения полигона к WServer"""
    print('settings status')
    command = "INSERT INTO {} (poligon, wserver_id, connected) values ((SELECT id FROM {} WHERE name='{}'), {}, True) " \
              "ON CONFLICT (poligon) " \
              "DO UPDATE set wserver_id={}, connected=True, upd_time='{}'"
    command = command.format(connection_status_table, pol_owners_table, poligon_name, wserver_id,
                             wserver_id, datetime.now())
    response = sqlshell.try_execute(command)
    print(response)
    print('done')


def set_wserver_disconnect_status(sqlshell, connection_status_table, pol_owners_table, poligon_name):
    """ Установить статус подключения полигона к WServer"""
    command = "INSERT INTO {} (poligon, connected) values ((SELECT id FROM {} WHERE name='{}'), False) " \
              "ON CONFLICT (poligon) " \
              "DO UPDATE set connected=False, upd_time='{}'"
    command = command.format(connection_status_table, pol_owners_table, poligon_name, datetime.now())
    sqlshell.try_execute(command)

def wserver_reconnecter(sqlshell, poligon_name, wserver_client, connection_status_table, pol_owners_table):
    connect_wserver(wserver_client)
    try:
        wserver_polygon_id = auth_me(wserver_client)
        send_act(wserver_client, wserver_polygon_id, sqlshell, connection_status_table, pol_owners_table,
                poligon_name)
    except:
        print(format_exc())
        set_wserver_disconnect_status(sqlshell, connection_status_table, pol_owners_table, poligon_name)

    while True:
        connection_status = fetch_wserver_connection_status(sqlshell, connection_status_table, pol_owners_table,
                                                            poligon_name)
        print('Connection status:', connection_status)
        if not connection_status:
            connect_wserver(wserver_client)
            try:
                wserver_polygon_id = auth_me(wserver_client)
                print("here {}. Poligon id".format(wserver_polygon_id))
                send_act(wserver_client, wserver_polygon_id, sqlshell, connection_status_table, pol_owners_table,
                         poligon_name)
            except:
                print(format_exc())
                set_wserver_disconnect_status(sqlshell, connection_status_table, pol_owners_table, poligon_name)
        else:
            pass
        sleep(15)


def send_act_by_polygon(connection_dict, sqlshell, connection_status_table, pol_owners_table):
    for pol_name, pol_info in connection_dict.items():
        wserver_id = fetch_wserver_id(sqlshell, pol_name, connection_status_table, pol_owners_table)
        send_act(connection_dict[pol_name]['wclient'], wserver_id, sqlshell,
                 connection_status_table, pol_owners_table, pol_name)

def launch_operation(connection_dict, sqlshell, connection_status_table, pol_owners_table):
    for pol_name, pol_info in connection_dict.items():
        wserver_id = fetch_wserver_id(sqlshell, pol_name, connection_status_table, pol_owners_table)
        send_act(connection_dict[pol_name]['wclient'], wserver_id, sqlshell,
                 connection_status_table, pol_owners_table, pol_name)


def fetch_wserver_id(sqlshell, pol_name, connection_status_table, pol_owners_table):
    command = "SELECT wserver_id FROM {} " \
              "INNER JOIN duo_pol_owners ON ({}.poligon={}.id) " \
              "WHERE {}.name='{}'".format(connection_status_table,
                                          connection_status_table, pol_owners_table,
                                          pol_owners_table, pol_name)
    wserver_id = sqlshell.try_execute_get(command)
    return wserver_id


def send_act(wserver_client, wserver_polygon_id, sqlshell, connection_status_table, pol_owners_table, poligon_name):
    """ Оотправить акты на SignAll"""
    print('\nОтправка актов на WServer')
    try:
        sig_funcs.send_json_reports(sqlshell, wserver_client, wserver_polygon_id,
                                    table_to_file_dict=s.json_table_to_file.items(), duo=True, pol_owner=poligon_name)
        set_wserver_connected_status(sqlshell, connection_status_table, pol_owners_table, poligon_name,
                                     wserver_polygon_id)
        print('\tАкты успешно отправлены')
    except:
        health_monitor.change_status('Связь с WServer', False, format_exc())
        print(format_exc())
        set_wserver_disconnect_status(sqlshell, connection_status_table, pol_owners_table, poligon_name)


def auth_me(wclient):
    # Попытаться авторизоваться
    response = auth_poligon(wclient)
    print('Результат авторизации', response)
    # Обработать ответ от WServer
    auth_result = operate_auth_info(response)
    health_monitor.change_status('Связь с WServer', True, 'Успешное подключение')
    return auth_result


def auth_poligon(wclient):
    """ Авторизовать полигон на WServer """
    data = wclient.auth_me()
    if type(data) == int:
        return data


def operate_auth_info(response):
    """ Обработать ответ от WServer на попытку авторизации """
    if response:
        return response
    else:
        health_monitor.change_status('Связь с WServer', False, 'Неправильный пароль')


def connect_wserver(wclient):
    # Попытаться подкючиться к WServer. Если успешно вернуть True, нет - внести изменения в health_monitor
    try:
        wclient.make_connection()
        return True
    except:
        health_monitor.change_status('Связь с WServer', False, format_exc())


def launch_wconnection_serv_daemon(sqlshell, all_poligons, connection_status_table, pol_owners_table):
    for poligon_name, poligon_info in all_poligons.items():
        threading.Thread(target=wserver_reconnecter, args=(sqlshell, poligon_name, poligon_info['wclient'],
                                                           connection_status_table, pol_owners_table)).start()
    print('All daemons has been launched')


def records_owning_save(sqlshell, records_owning_table, pol_owners_table, poligon_name, record_id):
    command = "INSERT INTO {} (record, owner) VALUES ({}, (SELECT id FROM {} WHERE name='{}')) " \
              "ON CONFLICT (record) DO NOTHING".format(records_owning_table, record_id, pol_owners_table, poligon_name)
    sqlshell.try_execute(command)
