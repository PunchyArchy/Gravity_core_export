import threading
from traceback import format_exc


def execute_api_method(core_method, *args, **kwargs):
    """ Выполнить метод core_method ядра core, передать ему аргументы """
    try:
        threading.Thread(target=core_method, args=args, kwargs=kwargs).start()
        response = {'status': 'success', 'info': 'Протокол заезда успешно начат'}
    except:
        response = {'status': 'failed', 'info': format_exc()}
    return response