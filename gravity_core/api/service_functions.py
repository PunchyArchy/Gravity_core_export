import threading


def execute_api_method(core, *args, **kwargs):
    try:
        threading.Thread(target=core.cic_start_car_protocol, args=args, kwargs=kwargs).start()
        response = {'status': 'success', 'info': 'Протокол заезда успешно начат'}
    except:
        response = {'status': 'failed', 'info': format_exc()}