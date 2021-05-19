""" Модуль, показывающий состояние всех подсистем Watchman-core """


# General status - словарь, содержащий основные подсистемы watchman-core и показывающие их статус.
# Если True - значит все работает; False - Проблемы, дополнительная информация под ключом info
general_status = {
                  'Подключение к FTP-серверу': {'status': True, 'info': 'Подключение стабильно'},
                  'Весовой терминал': {'status': True, 'info': 'Подключение стабильно'},
                  'Фотоэлементы': {'status': True, 'info': 'Подключение стабильно'},
                  'Связь с WServer': {'status': True, 'info': 'Подключение стабильно'}
                  }

def change_status(key, status, info='Нет информации'):
    # Операции по изменению показателя статуса
    general_status[key]['status'] = status
    general_status[key]['info'] = info


def get_monitor_info(*args, **kwargs):
    return general_status

