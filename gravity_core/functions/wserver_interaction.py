from gravity_core import health_monitor
from gravity_core import wsettings as s
from traceback import format_exc
from witapi.main import WITClient, WITServer


def create_wserver_connection():
    """ Создать подключение к WServer"""
    wclient = WITClient(s.wserver_ip, s.wserver_port, s.gdb_poligon_name, s.gdb_poligon_password, debug=s.WAPI_DEBUG)
    # Попытаться подключиться
    connection_result = connect_wserver(wclient)
    if connection_result:
        return wclient

def auth_me(wclient):
    # Попытаться авторизоваться
    response = auth_poligon(wclient)
    # Обработать ответ от WServer
    auth_result = operate_auth_info(response)
    health_monitor.change_status('Связь с WServer', True, 'Успешное подключение')
    return auth_result


def connect_wserver(wclient):
    # Попытаться подкючиться к WServer. Если успешно вернуть True, нет - внести изменения в health_monitor
    try:
        wclient.make_connection()
        return True
    except:
        health_monitor.change_status('Связь с WServer', False, format_exc())


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

def create_wserver_reciever():
    """ Создать сокет для приема данных от WServer """
    wserver_reciever = WITServer(s.my_ip, s.wserver_reciever_port, without_auth=True )
    wserver_reciever.launch_mainloop()
