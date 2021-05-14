""" Содержит инструменты для тестового режима"""

class SkudTestSocket():
    """ Эмулятор контроллера SKUD """
    def send(self, *args, **kwargs):
        print("Sigur SKUD testing socket.")
        print('SENDING {}'.format(args))

    def recv(self, *args, **kwargs):
        print("Sigur SKUD testing socket.")
        print("RECIEVING {}".format(args))

    def connect(self, *args, **kwargs):
        print("Sigur SKUD testing socket.")
        print("CONNECTING {}".format(kwargs))
