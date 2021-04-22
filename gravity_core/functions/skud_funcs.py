from time import sleep


def unsubscribe_ce(sock):
    '''Отписка от событий контроллера класса CE'''
    sleep(1)
    sock.send(b'"UNSUBSCRIBE" CE\r\n')


def unsubscribe_us(sock):
    '''Отписка от обычный событий контроллера'''
    sleep(1)
    sock.send(b'"UNSUBSCRIBE"\r\n')
    print('Статус оттписки us - ', get_response(sock))


def subscribe_ce(sock):
    sleep(1)
    sock.send(b'"SUBSCRIBE" CE\r\n')


def subscribe_us(sock):
    sleep(1)
    sock.send(b'"SUBSCRIBE"\r\n')


def resubscribe(sock):
    print('\nПереподписка')
    unsubscribe_ce(sock)
    subscribe_ce(sock)


def unsubscribe_us2(sock):
    '''Отписка без получения ответа'''
    sleep(1)
    sock.send(b'"UNSUBSCRIBE"\r\n')


def get_point_status(data):
    point = data[4]
    status = data[3]
    return point, status


def send_open_gate_command(sock, gate_num):
    msg = 'SETAPMODE UNLOCKED {}\r\n'.format(gate_num)
    sock.send(bytes(msg, encoding='utf-8'))


def send_close_gate_command(sock, gate_num):
    msg = 'SETAPMODE LOCKED {}\r\n'.format(gate_num)
    sock.send(bytes(msg, encoding='utf-8'))


def get_response(sock):
    return sock.recv(1024)


def make_connection(sock, ip, port):
    print('Подключение к контролеру скуд')
    sock.connect((ip, port))
    sock.send(b'"LOGIN" 1.8 "Administrator" ""\r\n')
    return get_response(sock)
