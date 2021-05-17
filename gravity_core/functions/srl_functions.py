""" Функции касаемо логгирования каждого заезда (Single Round Logging) """
import datetime
from gravity_core import wsettings as s
import os


def srl_create_file(carnum, opl_dirname):
    datetime = datetime.datetime.now()
    date = datetime.strftime(' %Y.%m.%d %H:%M:%S')
    file_name = carnum + ' ' + date
    pl_file = os.path.join(opl_dirname, file_name)
    with open(pl_file, 'w') as fobj:
        fobj.write('### CREATED NEW LOG FOR {} IN {} ###\n'.format(carnum, datetime))