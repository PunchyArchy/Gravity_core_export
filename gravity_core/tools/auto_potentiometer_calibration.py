from gravity_core.functions.skud_funcs import *
from socket import socket
from gravity_core import wsettings as s
from time import sleep
import threading

sock = socket()
make_connection(sock, s.contr_ip, s.contr_port)


def start_calibration(gate_num=1, count=10, sleeptime=5):
    while count != 0:
        send_open_gate_command(sock, gate_num)
        sleep(sleeptime)
        send_close_gate_command(sock, gate_num)
        count =- 1


def async_calibration_both_gates(gate_nums=[1,2], count=10, sleeptime=5):
    for gate_num in gate_nums:
        threading.Thread(target=start_calibration, args=(gate_num, count, sleeptime))

send_close_gate_command(sock, 1)
