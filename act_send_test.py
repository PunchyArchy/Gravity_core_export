from gravity_core.functions import duo_functions
from gravity_core import wsettings as s
from gravity_core.tests.sqlhell_test import shell
import threading


con_dict =  duo_functions.get_all_poligon_connections(shell, s.pol_owners_table, s.wserver_ip, s.wserver_port, True)
for pol_name, pol_info in con_dict.items():
    threading.Thread(target=duo_functions.wserver_reconnecter, args=(shell, pol_name, pol_info['wclient'], s.connection_status_table, s.pol_owners_table)).start()
