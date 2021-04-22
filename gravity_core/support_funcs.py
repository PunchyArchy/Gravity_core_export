from time import sleep
from gravity_core import wsettings as s


def photo_sender_thread(interval):
    while True:
        send_photos()
        sleep(interval)


def send_photos(ftp_gate):
    ftp_gate.open_connection()
    ftp_gate.move_to_dir('ftp/photos/')
    photo_sending(ftp_gate, s.fpath_file)
    ftp_gate.ftp.quit()


def photo_sending(ftp_gate, fpath_file):
    fpath = open(fpath_file, 'r')
    flis = []
    for rec in fpath.readlines():
        flis.append(rec)
    if len(flis) > 0:
        for rec in flis:
            if len(rec) > 1:
                rec = rec.replace('\n', '')
                ftp_gate.ftp_upload(rec, ftype='JPG')
    fpath.close()


def start_1c_data_importing(wbuh):
    wbuh.upd_cycle(s.clients_file_ftp, s.clients_localfile)


def get_rec_id(sqlshell, carnum):
    """ Генерирует и возвращает нужное название фотографии для заезда"""
    # Выяснить, что машина взвешивает - брутто или тару (начало или конец заезда)
    command = "SELECT id, inside FROM records WHERE car_number='{}' order by time_in desc limit 1".format(carnum)
    id_inside = sqlshell.try_execute_get(command)
    if len(id_inside) == 0:
        # нет информации по авто - новая заезжает
        course = 'IN'
        response = extract_last_id(sqlshell) + 1
    else:
        inside = id_inside[0][1]
        if inside == False:
            # Если машина заезжает, то достать последний ID + 1
            course = 'IN'
            response = extract_last_id(sqlshell) + 1
        else:
            # Если машина выезжает, то достать его id
            course = 'OUT'
            response = id_inside[0][0]
    record_id = str(response) + course
    return record_id


def extract_last_id(sqlshell):
    # Если машина заезжает, то достать последний ID + 1
    command = "select max(id) from records"
    try:
        response = sqlshell.try_execute_get(command)[0][0]
    except IndexError:
        # Если до этого не было заездов
        response = 1
    return response


def set_rfid_null(sqlshell, car_num):
    """ Назначить всем машинам с car_num значение rfid=null. Используется, когда метка была передана другой машине """
    command = "UPDATE auto SET rfid=null where car_number='{}'".format(car_num)
    sqlshell.try_execute(command)

def set_rfid_null_by_rfid(sqlshell, rfid):
    """ Назначить всем машинам с car_num значение rfid=null. Используется, когда метка была передана другой машине """
    command = "UPDATE auto SET rfid=null where rfid='{}'".format(rfid)
    sqlshell.try_execute(command)

def change_rfid(sqlshell, new_carnum, old_carnum):
    """ Если произошла смена владельца RFID-карты (в ОРУПе вбили другой гос.номер) - зарегать новую машину с меткой,
    у старой тачки выставить rfid=null."""

    # Фаза 1. Выяснить метку старой машины (она не может быть none по определению, ибо выявлена автоматически)
    old_car_rfid = sqlshell.get_rfid_by_carnum(old_carnum)[0][0]

    # Фаза 2. Отвязать старые метки от новой машины
    set_rfid_null(sqlshell, new_carnum)

    # Фаза3. А для старой выставить rfid = null
    set_rfid_null_by_rfid(sqlshell, old_car_rfid)

    # Фаза 4. Выясняем, была ли зарегана новая машина
    car_amount = get_car_amout(sqlshell, new_carnum)[0][0]
    if car_amount > 0:
        # Фаза 3.1 Если была уже зарегана - назначаем ей новую карту от старой машины (если она была зарегана)
        set_new_rfid(sqlshell, new_carnum, old_car_rfid)
        # Фаза 3.2 Если же нет - регестрируем ее с новой меткой




def get_car_amout(sqlshell, carnum):
    """ Возвращает количество машин с заданным гос.номером в таблице auto"""
    command = "SELECT count(car_number) from auto where car_number='{}'".format(carnum)
    response = sqlshell.try_execute_get(command)
    return response

def set_new_rfid(sqlshell, carnum, rfid):
    """ Выставить машине с гос.номером carnum новый RFID номер rfid """
    command = "UPDATE auto SET rfid='{}' WHERE car_number='{}'".format(rfid, carnum)
    sqlshell.try_execute(command)

def check_car_registered(sqlshell, carnum):
    """ Проверить регистрирована ли машина в таблице auto """
    command = "select exists(select car_number from auto where car_number='{}')".format(carnum)
    response = sqlshell.try_execute_get(command)
    response = response[0][0]
    if response:
        # Если транзакция удалась
        return response

def register_new_car(sqlshell, car_number):
    """ Зарегистрировать новую машину"""
    command = "insert into {} ".format(s.auto)
    command += "(car_number, id_type) "
    command += "values ('{}', 'tails')".format(car_number)
    sqlshell.try_execute(command)