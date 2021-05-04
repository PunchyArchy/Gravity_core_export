from gravity_core.functions import duo_functions
from gravity_core import wsettings as s
from gravity_core.tests.sqlhell_test import shell


con_dict =  duo_functions.get_all_poligon_connections(shell, s.pol_owners_table, s.wserver_ip, s.wserver_port, True)
duo_functions.send_act_by_polygon(con_dict, shell, s.connection_status_table, s.pol_owners_table)